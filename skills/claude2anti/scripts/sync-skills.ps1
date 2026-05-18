param(
    [ValidateSet("full", "single")]
    [string]$Mode = "full",

    [string]$SkillName = ""
)

$ErrorActionPreference = "Stop"

$targetRoot = Join-Path $env:USERPROFILE ".gemini\antigravity\skills"
$backupRoot = Join-Path $env:USERPROFILE ".gemini\antigravity\skill-backups"
$preserveNames = @(".system")

function Get-ClaudeSkillRoot {
    $fallback = Join-Path $env:USERPROFILE ".claude\skills"

    try {
        $claudePaths = & where.exe claude 2>$null
        if ($claudePaths) {
            foreach ($path in $claudePaths) {
                $resolved = $path.Trim()
                if (-not $resolved) {
                    continue
                }

                $parent = Split-Path -Parent $resolved
                if (-not $parent) {
                    continue
                }

                $candidate = Join-Path (Split-Path -Parent (Split-Path -Parent $parent)) ".claude\skills"
                if (Test-Path -LiteralPath $candidate) {
                    return $candidate
                }
            }
        }
    }
    catch {
    }

    return $fallback
}

function Normalize-SkillManifestCase {
    param(
        [Parameter(Mandatory = $true)][string]$SkillDir
    )

    $entries = Get-ChildItem -LiteralPath $SkillDir -Force -File | Select-Object -ExpandProperty Name
    $hasExactUpper = $entries -ccontains "SKILL.md"
    $hasExactLower = $entries -ccontains "skill.md"
    $temp = Join-Path $SkillDir "__skill_manifest_tmp__.md"
    $upper = Join-Path $SkillDir "SKILL.md"
    $lower = Join-Path $SkillDir "skill.md"

    if ($hasExactLower -and -not $hasExactUpper) {
        Move-Item -LiteralPath $lower -Destination $temp -Force
        Move-Item -LiteralPath $temp -Destination $upper -Force
        return "normalized-to-upper"
    }

    if ($hasExactUpper) {
        return "already-normalized"
    }

    return "manifest-missing"
}

function New-BackupDir {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupDir = Join-Path $backupRoot $timestamp
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    return $backupDir
}

function Copy-SkillItem {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$TargetPath
    )

    if (Test-Path -LiteralPath $TargetPath) {
        Remove-Item -LiteralPath $TargetPath -Recurse -Force
    }

    $item = Get-Item -LiteralPath $SourcePath -Force

    if ($item.LinkType) {
        $realTarget = $item.Target
        if ($realTarget -is [array]) {
            $realTarget = $realTarget[0]
        }
        $item = Get-Item -LiteralPath $realTarget -Force
    }

    if ($item.PSIsContainer) {
        New-Item -ItemType Directory -Force -Path $TargetPath | Out-Null

        Get-ChildItem -LiteralPath $item.FullName -Force | ForEach-Object {
            $childTargetName = $_.Name
            if ($_.PSIsContainer -eq $false -and (($_.Name -ceq "skill.md") -or ($_.Name -ceq "SKILL.md"))) {
                $childTargetName = "SKILL.md"
            }

            $childTargetPath = Join-Path $TargetPath $childTargetName

            if ($_.PSIsContainer) {
                Copy-SkillItem -SourcePath $_.FullName -TargetPath $childTargetPath | Out-Null
            }
            else {
                Copy-Item -LiteralPath $_.FullName -Destination $childTargetPath -Force
            }
        }

        return "directory-copy"
    }

    Copy-Item -LiteralPath $item.FullName -Destination $TargetPath -Force
    return "file-copy"
}

function Confirm-SyncResult {
    param(
        [Parameter(Mandatory = $true)]$SyncedItems,
        [Parameter(Mandatory = $true)][string]$SourceRootPath,
        [Parameter(Mandatory = $true)][string]$TargetRootPath
    )

    $verifyErrors = @()

    foreach ($item in $SyncedItems) {
        $srcPath = Join-Path $SourceRootPath $item.name
        $tgtPath = Join-Path $TargetRootPath $item.name

        if (-not (Test-Path -LiteralPath $tgtPath)) {
            $verifyErrors += "Verification failed: target missing for '$($item.name)'"
            continue
        }

        $manifest = Join-Path $tgtPath "SKILL.md"
        if (-not (Test-Path -LiteralPath $manifest)) {
            $manifest = Join-Path $tgtPath "skill.md"
            if (-not (Test-Path -LiteralPath $manifest)) {
                $verifyErrors += "Verification failed: SKILL.md missing for '$($item.name)'"
                continue
            }
        }

        $srcFiles = (Get-ChildItem -LiteralPath $srcPath -File -Recurse -Force | Measure-Object).Count
        $tgtFiles = (Get-ChildItem -LiteralPath $tgtPath -File -Recurse -Force | Measure-Object).Count
        if ($srcFiles -ne $tgtFiles) {
            $verifyErrors += "Verification failed: file count mismatch for '$($item.name)' (source=$srcFiles, target=$tgtFiles)"
        }
    }

    return $verifyErrors
}

function Ensure-Roots {
    $script:sourceRoot = Get-ClaudeSkillRoot

    if (-not (Test-Path -LiteralPath $sourceRoot)) {
        throw "Source skills directory not found: $sourceRoot"
    }

    if (-not (Test-Path -LiteralPath $targetRoot)) {
        New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
    }

    if (-not (Test-Path -LiteralPath $backupRoot)) {
        New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
    }
}

Ensure-Roots

$result = [ordered]@{
    mode = $Mode
    source_root = $sourceRoot
    target_root = $targetRoot
    backup_dir = $null
    synced = @()
    skipped = @()
    errors = @()
}

try {
    $backupDir = New-BackupDir
    $result.backup_dir = $backupDir

    if ($Mode -eq "full") {
        Get-ChildItem -LiteralPath $targetRoot -Force | ForEach-Object {
            if ($preserveNames -contains $_.Name) {
                $result.skipped += $_.Name
                return
            }

            Move-Item -LiteralPath $_.FullName -Destination $backupDir
        }

        Get-ChildItem -LiteralPath $sourceRoot -Force | ForEach-Object {
            $targetPath = Join-Path $targetRoot $_.Name
            $copyMode = Copy-SkillItem -SourcePath $_.FullName -TargetPath $targetPath
            $manifestMode = "not-a-directory"
            if (Test-Path -LiteralPath $targetPath -PathType Container) {
                $manifestMode = Normalize-SkillManifestCase -SkillDir $targetPath
            }
            $result.synced += [ordered]@{
                name = $_.Name
                copy_mode = $copyMode
                manifest_mode = $manifestMode
            }
        }
    }
    elseif ($Mode -eq "single") {
        if ([string]::IsNullOrWhiteSpace($SkillName)) {
            throw "SkillName is required when Mode=single"
        }

        $sourcePath = Join-Path $sourceRoot $SkillName
        if (-not (Test-Path -LiteralPath $sourcePath)) {
            throw "Source skill not found: $sourcePath"
        }

        $targetPath = Join-Path $targetRoot $SkillName
        if (Test-Path -LiteralPath $targetPath) {
            Move-Item -LiteralPath $targetPath -Destination $backupDir
        }

        $copyMode = Copy-SkillItem -SourcePath $sourcePath -TargetPath $targetPath
        $manifestMode = "not-a-directory"
        if (Test-Path -LiteralPath $targetPath -PathType Container) {
            $manifestMode = Normalize-SkillManifestCase -SkillDir $targetPath
        }
        $result.synced += [ordered]@{
            name = $SkillName
            copy_mode = $copyMode
            manifest_mode = $manifestMode
        }
    }
}
catch {
    $result.errors += $_.Exception.Message
}

if ($result.errors.Count -eq 0 -and $result.synced.Count -gt 0) {
    $verifyErrors = Confirm-SyncResult -SyncedItems $result.synced -SourceRootPath $sourceRoot -TargetRootPath $targetRoot
    if ($verifyErrors.Count -gt 0) {
        $result.errors += $verifyErrors
        $result.errors += "Backup preserved at: $($result.backup_dir) - do not delete manually until verified"
    }
}

if ($result.errors.Count -eq 0 -and $result.backup_dir) {
    try {
        Remove-Item -LiteralPath $result.backup_dir -Recurse -Force
        $result.backup_dir = $null
    }
    catch {
        $result.errors += "Sync completed but failed to remove backup dir '$($result.backup_dir)': $($_.Exception.Message)"
    }
}

$result | ConvertTo-Json -Depth 6
