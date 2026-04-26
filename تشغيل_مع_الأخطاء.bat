' نظام إدارة الموظفين - برنامج التشغيل (نسخة تصحيح الأخطاء)
' يعرض جميع الأخطاء بوضوح

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' الحصول على مسار المجلد الحالي
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' التحقق من وجود ملف run_app_debug.py
strPythonScript = strScriptPath & "\run_app_debug.py"
If Not objFSO.FileExists(strPythonScript) Then
    MsgBox "خطأ: لم يتم العثور على ملف run_app_debug.py" & vbCrLf & "المسار: " & strPythonScript, vbCritical, "خطأ"
    WScript.Quit
End If

' التحقق من وجود app.py
strAppFile = strScriptPath & "\app.py"
If Not objFSO.FileExists(strAppFile) Then
    MsgBox "خطأ: لم يتم العثور على ملف app.py" & vbCrLf & "المسار: " & strAppFile, vbCritical, "خطأ"
    WScript.Quit
End If

' التحقق من وجود emp.db
strDbFile = strScriptPath & "\emp.db"
If Not objFSO.FileExists(strDbFile) Then
    MsgBox "خطأ: لم يتم العثور على ملف emp.db" & vbCrLf & "المسار: " & strDbFile, vbCritical, "خطأ"
    WScript.Quit
End If

' تشغيل ملف Python (مع عرض نافذة الأوامر لرؤية الأخطاء)
' تشغيل ملف Python وإخفاء نافذة الأوامر تماماً
objShell.Run "pythonw """ & strPythonScript & """", 0, False
