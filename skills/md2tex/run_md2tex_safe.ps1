param(
  [Parameter(Mandatory=$true)][string]$InputMd,
  [string]$OutputDir = '',
  [switch]$FixMathBackticks
)
$pre='C:\Users\20174\.codex\skills\md2tex\md_math_precheck.py'
$core='C:\Users\20174\.codex\skills\md2tex\md2tex.py'
if($FixMathBackticks){
  python $pre $InputMd --fix
}else{
  python $pre $InputMd
  if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE }
}
if([string]::IsNullOrWhiteSpace($OutputDir)){
  python $core $InputMd
}else{
  python $core $InputMd --output-dir $OutputDir
}
