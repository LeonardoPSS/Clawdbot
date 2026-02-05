$TaskName = "ClawdbotAutoWake"
$ScriptPath = "C:\Users\leona\Downloads\AntigravityJobBot\start_bot.ps1"
$Time = "08:00"

Write-Host "Configuring Clawdbot to wake PC daily at $Time..."

# Define Action: Run the bot script
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

# Define Trigger: Daily at 08:00
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

# Define Settings: Wake to run
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -Priority 1

# Register Task
# Note: Needs Admin privileges usually, but might work for user scope if they have permission to wake.
# Using -User "SYSTEM" or current user.
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -User $env:USERNAME -Force
    Write-Host "✅ Sucesso! O PC vai acordar todo dia as $Time para rodar o Clawdbot."
    Write-Host "⚠️ IMPORTANTE: Não desligue o PC. Use 'Suspender' ou 'Hibernar'."
}
catch {
    Write-Error "Falha ao criar tarefa: $_"
    Write-Host "Tente rodar o PowerShell como Administrador."
}
