param(
    [Parameter(Mandatory=$true)][string]$Pythonw,
    [switch]$Enable,
    [switch]$AllowLoginOnly
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pythonPath = (Resolve-Path -LiteralPath $Pythonw).Path
$entry = Join-Path $PSScriptRoot 'run_local.py'
if (!(Test-Path -LiteralPath $entry)) { throw 'Runner entry point is missing' }
$name = 'JobFinder-Local'
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
    throw 'Task already exists; inspect it before replacing it'
}
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument ('"{0}" --due' -f $entry) -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 5)
$startup = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$logonType = if ($AllowLoginOnly) { 'Interactive' } else { 'S4U' }
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType $logonType -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger @($trigger, $startup) -Settings $settings -Principal $principal
$task.Settings.Enabled = [bool]$Enable
try {
    Register-ScheduledTask -TaskName $name -InputObject $task -ErrorAction Stop | Select-Object TaskName,State
} catch {
    Write-Error 'Task registration failed. Run elevated for independent execution, or pass -AllowLoginOnly for the login-bound fallback. The old scheduler remains active.' -ErrorAction Continue
    exit 1
}
