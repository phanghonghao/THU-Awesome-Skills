param(
  [Parameter(Mandatory=$true)][string]$InputMd,
  [string]$OutputDir = '',
  [switch]$FixMathBackticks
)
$pre='<SKILL_ROOT>\md2tex\md_math_precheck.py'
$core='<SKILL_ROOT>\md2tex\md2tex.py'
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
