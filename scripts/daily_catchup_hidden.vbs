' Launches daily_catchup.cmd with no visible console window.
' Window style 0 = hidden; the .cmd still redirects output to data\daily_catchup.log.
Set sh = CreateObject("WScript.Shell")
sh.Run "cmd /c ""C:\Project\newsNblog\scripts\daily_catchup.cmd""", 0, False
