Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptPath = WScript.ScriptFullName
scriptFolder = fso.GetParentFolderName(scriptPath)
cmd = """" & scriptFolder & "\run.bat" & """"
objShell.Run cmd, 0, False
