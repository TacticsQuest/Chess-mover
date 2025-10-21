$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Chess Mover Machine.lnk")
$Shortcut.TargetPath = "C:\Windows\System32\pythonw.exe"
$Shortcut.Arguments = "`"C:\Users\David\Documents\GitHub\Chess Mover Machine\main.py`""
$Shortcut.WorkingDirectory = "C:\Users\David\Documents\GitHub\Chess Mover Machine"
$Shortcut.Description = "Chess Mover Machine Control Software"
$Shortcut.Save()
Write-Host "Shortcut created on Desktop!"
