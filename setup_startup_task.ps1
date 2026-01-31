# PowerShell script to create a Windows Task Scheduler task for the LinkedIn Bot
$TaskName = "AntigravityLinkedInBot"
$TaskDescription = "Runs the Clawdbot LinkedIn automation on startup"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\Users\leona\Downloads\AntigravityJobBot\start_bot.ps1" -WorkingDirectory $WorkingDirectory

# 2. Create the trigger (At Log On)
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# 3. Create the settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 30)

# 4. Register the task (Force overwrite if exists)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description $TaskDescription -Force

Write-Host "✅ Task Scheduler entry created successfully: $TaskName"
Write-Host "🚀 The bot will now start automatically whenever you log into Windows."
