# PowerShell script to create a shortcut to start the Coffee Chat Discord bot
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Start Coffee Chat Bot.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"C:\Users\lhamr\OneDrive\Desktop\autoxi\coffee_bot\start_coffee_bot.ps1`""
$Shortcut.WorkingDirectory = "C:\Users\lhamr\OneDrive\Desktop\autoxi\coffee_bot"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Description = "Start Coffee Chat Discord Bot"
$Shortcut.Save()

Write-Host "Shortcut created on your desktop: 'Start Coffee Chat Bot.lnk'"
