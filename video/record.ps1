# Records the terminal act as one continuous take: ffmpeg grabs the 1600x900
# region the demo windows are placed in, then launches the demo console.
$root = "C:\Hackathons\Sibyl Hackathon\video"
New-Item -ItemType Directory -Force "$root\clips" | Out-Null
$ff = Start-Process ffmpeg -ArgumentList @(
  "-y", "-f", "gdigrab", "-framerate", "15", "-offset_x", "0", "-offset_y", "0", "-video_size", "1600x900",
  "-i", "desktop", "-t", "222", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
  "$root\clips\terminal.mp4") -PassThru -WindowStyle Hidden
Start-Sleep 2
Start-Process conhost -ArgumentList "powershell -NoExit -ExecutionPolicy Bypass -File `"$root\demo.ps1`""
$ff.WaitForExit()
Get-Process | Where-Object { $_.MainWindowTitle -like "NERACA*" } | Stop-Process -Force -ErrorAction SilentlyContinue
"recorded: $root\clips\terminal.mp4"
