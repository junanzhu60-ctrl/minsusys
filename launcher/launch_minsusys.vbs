Option Explicit

Dim shell, fileSystem, launcherFolder, scriptPath, command
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

launcherFolder = fileSystem.GetParentFolderName(WScript.ScriptFullName)
scriptPath = fileSystem.BuildPath(launcherFolder, "start_minsusys.ps1")
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & scriptPath & """"

' 0 means the launcher itself never shows a command-window.
shell.Run command, 0, False
