Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = "C:\Users\MSI\Downloads\test 1"
WshShell.CurrentDirectory = strDir

pythonwPath = "C:\Python314\pythonw.exe"
If Not fso.FileExists(pythonwPath) Then
    pythonwPath = "pythonw.exe"
End If

WshShell.Run """" & pythonwPath & """ """ & strDir & "\idm_service.py""", 0, False
