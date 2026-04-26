Dim objShell, objFSO
Dim strScriptPath, strPythonScript, strAppFile, strDbFile, strPythonExe, strCommand

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

strPythonExe = "C:\Program Files\Python314\python.exe"
strPythonScript = strScriptPath & "\run_app_debug.py"
strAppFile = strScriptPath & "\app.py"
strDbFile = strScriptPath & "\emp.db"

If Not objFSO.FileExists(strPythonExe) Then
    MsgBox "Python not found:" & vbCrLf & strPythonExe, vbCritical
    WScript.Quit
End If

If Not objFSO.FileExists(strPythonScript) Then
    MsgBox "run_app_debug.py not found:" & vbCrLf & strPythonScript, vbCritical
    WScript.Quit
End If

If Not objFSO.FileExists(strAppFile) Then
    MsgBox "app.py not found:" & vbCrLf & strAppFile, vbCritical
    WScript.Quit
End If

If Not objFSO.FileExists(strDbFile) Then
    MsgBox "emp.db not found:" & vbCrLf & strDbFile, vbCritical
    WScript.Quit
End If

' 👇 الحل هنا
strCommand = "cmd /k """"" & strPythonExe & """ """ & strPythonScript & """"""

objShell.Run strCommand, 0, False