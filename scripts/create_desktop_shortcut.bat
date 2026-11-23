@echo off
echo =======================================================
echo   Creating Instant Toggle Desktop Shortcut (Ctrl+Alt+T)
echo =======================================================

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell;" ^
    "$desktopPath = [System.Environment]::GetFolderPath('Desktop');" ^
    "$Shortcut = $WshShell.CreateShortcut(\"$desktopPath\Toggle Theme.lnk\");" ^
    "$pythonw = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source;" ^
    "if (-not $pythonw) { $pythonw = 'pythonw.exe' };" ^
    "$scriptPath = Join-Path (Get-Location).Path 'scripts\toggle_theme.py';" ^
    "$Shortcut.TargetPath = $pythonw;" ^
    "$Shortcut.Arguments = \"`\"$scriptPath`\"\";" ^
    "$Shortcut.WorkingDirectory = (Get-Location).Path;" ^
    "$Shortcut.Hotkey = 'Ctrl+Alt+T';" ^
    "$Shortcut.IconLocation = 'themecpl.dll,0';" ^
    "$Shortcut.Description = 'Toggle Windows Light/Dark Theme via Python (Ctrl+Alt+T)';" ^
    "$Shortcut.Save();" ^
    "Write-Output 'Shortcut successfully created on Desktop!'"

pause
