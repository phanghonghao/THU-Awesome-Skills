param(
    [Parameter(Mandatory = $true)]
    [string]$VideoUrl,

    [string]$PythonExe = "python",

    [switch]$ForFeishu
)

$ErrorActionPreference = "Stop"

$args = @("scripts\bilibili_embodied_ai_pipeline.py", $VideoUrl)
if ($ForFeishu) {
    $args += "--for-feishu"
}

& $PythonExe @args
