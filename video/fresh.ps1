# The fresh session: a brand-new process, opened on camera, that never saw
# the rejection - and cites it anyway. Closes itself after the recall beat.
Add-Type -Namespace Win -Name Con2 -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
[DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool r);
[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int n);
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct FONT { public uint cbSize; public uint nFont; public short X; public short Y; public int FontFamily; public int FontWeight; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string FaceName; }
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool SetCurrentConsoleFontEx(IntPtr h, bool max, ref FONT f);
'@
$f = New-Object Win.Con2+FONT
$f.cbSize = [System.Runtime.InteropServices.Marshal]::SizeOf($f); $f.nFont = 0; $f.X = 0; $f.Y = 22
$f.FontFamily = 54; $f.FontWeight = 400; $f.FaceName = "Consolas"
[Win.Con2]::SetCurrentConsoleFontEx([Win.Con2]::GetStdHandle(-11), $false, [ref]$f) | Out-Null
$host.UI.RawUI.BackgroundColor = "DarkBlue"; $host.UI.RawUI.ForegroundColor = "White"; Clear-Host
[Win.Con2]::MoveWindow([Win.Con2]::GetConsoleWindow(), 40, 40, 1520, 820, $true) | Out-Null
$host.UI.RawUI.WindowTitle = "NERACA - fresh session"

Set-Location "C:\Hackathons\Sibyl Hackathon"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\.venv\Scripts\Activate.ps1
$env:NERACA_DB = "./data/demo.db"

Write-Host "# NEW PROCESS - pid $PID - this session never saw the rejection." -ForegroundColor Yellow
Write-Host ("commit " + (git rev-parse --short HEAD) + "   " + (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss 'UTC'")) -ForegroundColor Green
Start-Sleep 3
Write-Host ""; Write-Host "> python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50" -ForegroundColor Cyan
python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50
Start-Sleep 8
Write-Host ""; Write-Host "> python -m neraca report 0xKLIENB000000000000000000000000000000000B" -ForegroundColor Cyan
python -m neraca report 0xKLIENB000000000000000000000000000000000B
Write-Host ""; Write-Host "# It cites the rejection anyway. That is the gate." -ForegroundColor Yellow
Start-Sleep 12
exit
