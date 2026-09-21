param(
    [Parameter(Mandatory=$true)][string]$Pythonw,
    [switch]$EnableNow
)
$ErrorActionPreference = 'Stop'
$pythonPath = (Resolve-Path -LiteralPath $Pythonw).Path
$entry = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'run_local.py')).Path
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$backup = Join-Path $startup ('JobFinder-disabled-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
$old = Get-ChildItem -LiteralPath $startup -Filter '*.lnk' | Where-Object { $_.Name -match 'JobFinder|GitHub Actions Runner' }
foreach ($shortcut in $old) {
    Move-Item -LiteralPath $shortcut.FullName -Destination $backup -Force
}
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $startup 'JobFinder Local Runner.lnk'))
$shortcut.TargetPath = $pythonPath
$shortcut.Arguments = ('"{0}" --loop' -f $entry)
$shortcut.WorkingDirectory = (Split-Path -Parent $PSScriptRoot)
$shortcut.WindowStyle = 7
$shortcut.Save()
if ($EnableNow) {
    Start-Process -FilePath $pythonPath -ArgumentList ('"{0}" --loop' -f $entry) -WorkingDirectory $shortcut.WorkingDirectory -WindowStyle Hidden
}
Get-Item (Join-Path $startup 'JobFinder Local Runner.lnk') | Select-Object FullName
