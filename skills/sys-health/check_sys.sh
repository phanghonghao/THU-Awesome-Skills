#!/usr/bin/env bash
# UniLab System Health Check
# ----------------------------------------------------------------------------
# Single script that probes BOTH sides of this machine:
#   - WSL Ubuntu (where RL training actually runs, CPU-only)
#   - Windows    (host CPU/disk/GPU, via powershell.exe interop)
#
# Run from WSL. A single failing probe never aborts the whole report.
#
# Usage:
#   wsl -d Ubuntu -u u20174 -- bash -c \
#     "tr -d '\r' < /mnt/c/Users/20174/.claude/skills/sys-health/check_sys.sh | bash"
# (tr -d '\r' makes it immune to CRLF that Windows editors may introduce.)

set +e

hr() { printf '\n================  %s  ================\n' "$1"; }

# ============================================================
# WSL / Linux side
# ============================================================
hr "HOST"
echo "Kernel : $(uname -r 2>/dev/null)"
echo "Uptime : $(uptime -p 2>/dev/null || uptime)"
echo "Load   : $(awk '{print $1, $2, $3}' /proc/loadavg 2>/dev/null)  (1/5/15 min)"

hr "CPU (model)"
grep -m1 'model name' /proc/cpuinfo 2>/dev/null | sed 's/^model name[[:space:]]*: //'
cores=$(nproc 2>/dev/null)
echo "Logical cores: ${cores:-?}  (load > cores => oversubscribed)"

hr "CPU LIVE FREQUENCY (MHz per logical core)"
freqs=$(for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; do
          [ -f "$f" ] && awk '{printf "%d ", $1/1000}' "$f"
        done)
echo "${freqs:-(cpufreq not exposed in WSL2)}"

hr "MEMORY & SWAP"
free -h 2>/dev/null || echo "(free not available)"
memwarn=$(free -m 2>/dev/null | awk '/^Mem:/{a=$7} END{ if(a+0 < 1024) print "WARNING: low available RAM (<1GB) — training may spill to swap/SSD"; }')
[ -n "$memwarn" ] && echo "$memwarn"
swapused=$(free -m 2>/dev/null | awk '/^Swap:/{print $3}')
[ -n "${swapused:-}" ] && [ "$swapused" -gt 0 ] 2>/dev/null && echo "NOTE: ${swapused}MB swap in use (writing to disk)"

hr "DISK USAGE (WSL ext4 = vhdx on Windows drive)"
df -h / 2>/dev/null

hr "TOP CPU PROCESSES (is a training run active?)"
ps -eo pid,user,%cpu,%mem,etime,comm --sort=-%cpu 2>/dev/null | head -n 7

hr "THERMAL ZONES (WSL2 virtual kernel — usually empty)"
zones=""
for z in /sys/class/thermal/thermal_zone*; do
  [ -f "$z/temp" ] || continue
  zones="$zones$(cat "$z/type" 2>/dev/null): $(awk '{printf "%.1f C", $1/1000}' "$z/temp")\n"
done
[ -n "$zones" ] && printf '%b' "$zones" || echo "(none — WSL2 does not expose host CPU temp; check WINDOWS CPU TEMP below)"

hr "TRAINING WRITE ACTIVITY (writes stress the SSD lifetime)"
ULAB="$HOME/UniLab"
if [ -d "$ULAB/logs" ]; then
  echo "Files modified in logs/ within last 10 min:"
  recent=$(find "$ULAB/logs" -type f -mmin -10 2>/dev/null | head -n 15)
  [ -n "$recent" ] && echo "$recent" || echo "  (none — no active writes)"
  ptcount=$(find "$ULAB" -name '*.pt' 2>/dev/null | wc -l)
  echo "Total .pt checkpoints stored: ${ptcount}"
  ptsize=$(find "$ULAB" -name '*.pt' -printf '%s\n' 2>/dev/null | awk '{s+=$1} END{printf "%.1f", s/1024/1024/1024}')
  echo "Total checkpoint size      : ${ptsize} GB"
else
  echo "($ULAB/logs not found — no UniLab clone at expected path)"
fi

hr "NVMe SMART (SSD wear — needs nvme-cli)"
if command -v nvme >/dev/null 2>&1; then
  for dev in /dev/nvme0n1; do
    [ -b "$dev" ] && sudo -n nvme smart-log "$dev" 2>/dev/null \
      | grep -iE 'temperature|data_units_(read|written)|power_on_hours' \
      || echo "(needs sudo to read SMART)"
  done
  [ -b /dev/nvme0n1 ] || echo "(no nvme block device)"
else
  echo "nvme-cli not installed ->  sudo apt install nvme-cli   (then re-run)"
fi

# ============================================================
# Windows host side (powershell.exe via WSL interop)
# ============================================================
# Gotcha: powershell.exe inherits the bash pipe stdin and BLOCKS waiting for it.
# Fix: redirect stdin from /dev/null on every call. Wrap in a helper.
# \$ inside the command keeps bash from expanding powershell's own $ vars.
psq() {
  timeout 25 powershell.exe -NoProfile -NonInteractive -Command "$1" </dev/null 2>/dev/null \
    | tr -d '\r' | grep -v '^[[:space:]]*$'
}

hr "WINDOWS CPU"
psq "Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,LoadPercentage,CurrentClockSpeed,MaxClockSpeed | Format-List | Out-String"

hr "WINDOWS MEMORY"
psq "\$o=Get-CimInstance Win32_OperatingSystem; 'Total(GB): '+[math]::Round(\$o.TotalVisibleMemorySize/1MB,2); 'Free (GB): '+[math]::Round(\$o.FreePhysicalMemory/1MB,2); 'Used (GB): '+[math]::Round((\$o.TotalVisibleMemorySize-\$o.FreePhysicalMemory)/1MB,2)"

hr "WINDOWS PHYSICAL DISKS"
psq "Get-CimInstance Win32_DiskDrive | Select-Object Model,@{n='Size_GB';e={[math]::Round(\$_.Size/1GB)}},Status | Format-Table -AutoSize | Out-String -Width 200"

hr "WINDOWS VOLUMES (drive usage)"
psq "Get-Volume | Where-Object {\$_.DriveLetter} | Select-Object DriveLetter,@{n='Size_GB';e={[math]::Round(\$_.Size/1GB)}},@{n='Free_GB';e={[math]::Round(\$_.SizeRemaining/1GB)}} | Format-Table -AutoSize | Out-String -Width 200"

hr "WINDOWS GPU"
psq "Get-CimInstance Win32_VideoController | Select-Object Name,@{n='VRAM_MB';e={[math]::Round(\$_.AdapterRAM/1MB)}} | Format-List | Out-String"

hr "WINDOWS CPU TEMP (auto-detect LibreHardwareMonitor / OpenHardwareMonitor)"
psq "\$found=\$false; foreach(\$ns in @('LibreHardwareMonitor','OpenHardwareMonitor')){ try { \$s=Get-CimInstance -Namespace (\"root/\"+\$ns) -ClassName Sensor -ErrorAction Stop | Where-Object {\$_.SensorType -eq 'Temperature'}; if(\$s){ \$found=\$true; \$s | Select-Object Name,@{n='Temp_C';e={[math]::Round(\$_.Value,0)}} | Format-Table -AutoSize | Out-String -Width 200 } } catch {} }; if(-not \$found){ 'NOT available: install LibreHardwareMonitor, run it, and enable its WMI provider to read CPU temp.' }"

hr "HEALTH CHECK DONE"
echo "Interpretation guide is in SKILL.md."
