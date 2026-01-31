Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.ExpandEnvironmentStrings("%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AntigravityBot.lnk")
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\Users\leona\Downloads\AntigravityJobBot\start_bot.cmd"
oLink.WorkingDirectory = "C:\Users\leona\Downloads\AntigravityJobBot"
oLink.Description = "Inicia o bot do LinkedIn automaticamente ao ligar o PC"
oLink.Save
WScript.Echo "✅ Atalho de inicialização criado com sucesso!"
