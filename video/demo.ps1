# NERACA demo - the terminal act, recorded as one continuous take.
# Every command is real; every output is what it printed. Act starts are pinned
# to fixed seconds so the narration lines up.
param([int]$FontSize = 22)

Add-Type -Namespace Win -Name Con -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern IntPtr GetConsoleWindow();
[DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool r);
[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int n);
[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
public struct FONT { public uint cbSize; public uint nFont; public short X; public short Y; public int FontFamily; public int FontWeight; [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string FaceName; }
[DllImport("kernel32.dll", SetLastError = true)] public static extern bool SetCurrentConsoleFontEx(IntPtr h, bool max, ref FONT f);
'@
$f = New-Object Win.Con+FONT
$f.cbSize = [System.Runtime.InteropServices.Marshal]::SizeOf($f); $f.nFont = 0; $f.X = 0; $f.Y = [int16]$FontSize
$f.FontFamily = 54; $f.FontWeight = 400; $f.FaceName = "Consolas"
[Win.Con]::SetCurrentConsoleFontEx([Win.Con]::GetStdHandle(-11), $false, [ref]$f) | Out-Null
$host.UI.RawUI.BackgroundColor = "Black"; $host.UI.RawUI.ForegroundColor = "Gray"; Clear-Host
[Win.Con]::MoveWindow([Win.Con]::GetConsoleWindow(), 0, 0, 1600, 900, $true) | Out-Null
$host.UI.RawUI.WindowTitle = "NERACA demo"

Set-Location "C:\Hackathons\Sibyl Hackathon"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\.venv\Scripts\Activate.ps1
$env:NERACA_DB = "./data/demo.db"
Remove-Item data\demo.db* -Force -ErrorAction SilentlyContinue

$script:T0 = Get-Date
function At([int]$sec) { $wait = $sec - ((Get-Date) - $script:T0).TotalSeconds; if ($wait -gt 0) { Start-Sleep -Milliseconds ([int]($wait * 1000)) } }
function Say([string]$t) { Write-Host ""; Write-Host "# $t" -ForegroundColor Yellow }
function Run([string]$cmd) { Write-Host ""; Write-Host "> $cmd" -ForegroundColor Cyan; Invoke-Expression $cmd }
function Stamp() { Write-Host ("commit " + (git rev-parse --short HEAD) + "   " + (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss 'UTC'")) -ForegroundColor Green }

# ---- act 1: problem (0s) ----
Say "NERACA - a trust bureau for the agent economy."
Say "Agents hire each other on Virtuals ACP and settle USDC on Base. Nothing remembers who burned whom."
Stamp

# ---- act 2: the journal grows, the verdict moves (12s) ----
At 12
Say "Three agents, one shared Sibyl Memory, no other channel. PENGAMAT journals 27 observations:"
Run "python -m neraca seed --before-dispute"
At 18
Run "python -m neraca analis"
At 24
Say "Same budget, two clients. The premium comes straight from what memory holds."
Run "python -m neraca ask 0xKLIENA000000000000000000000000000000000A --budget 50"
At 33
Run "python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50"
At 42
Say "Now PENGAMAT witnesses ONE event: KLIEN-B rejects a delivered job."
Run "python -m neraca witness"
At 48
Run "python -m neraca analis"
At 53
Run "python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50"
At 62
Say "The code did not change. The memory did."

# ---- act 3: fresh session, one continuous take (66s) ----
At 66
Say "Fresh session. A NEW terminal process that never saw the rejection:"
Start-Process conhost -ArgumentList 'powershell -NoExit -ExecutionPolicy Bypass -File "C:\Hackathons\Sibyl Hackathon\video\fresh.ps1"' | Out-Null
At 100

# ---- act 4: deletion test (100s) ----
Say "The deletion test. No memory, no bureau - there is nothing to fall back to:"
Run '$env:NERACA_MEMORY_DISABLED="1"; python -m neraca ask 0xKLIENB000000000000000000000000000000000B --budget 50; Write-Host "exit code $LASTEXITCODE"; Remove-Item Env:NERACA_MEMORY_DISABLED'

# ---- act 5: the bureau grades itself (110s) ----
At 110
Say "The bureau grades its own verdicts and revises its doctrine - the rubric lives in REFERENCE memory:"
Run "python -m neraca reflect"
At 120
Run "python -m neraca analis"
At 126
Run "python -m neraca reflect"

# ---- act 6: selling the answer, on-chain (132s) ----
At 132
Say "Selling the answer. The USDC stake is gated by memory: refused for KLIEN-B, fired for KLIEN-A."
Run "python -m neraca.onchain stake 0xKLIENB000000000000000000000000000000000B 1.0"
At 140
Run "python -m neraca ask 0xKLIENA000000000000000000000000000000000A --budget 50 | Select-Object -First 4"
At 146
Run "python -m neraca.onchain stake 0xKLIENA000000000000000000000000000000000A 1.0"
At 172
Say "Real agents, real jobs: PENGAMAT reads the live ACP contracts on Base mainnet. No keys."
Run "python -m neraca chain --lookback 4000"
At 186
Run "python -m neraca analis | Select-Object -First 6"

# ---- close (194s) ----
At 194
Say "21 tests, one of them the deletion test judges run themselves. github.com/PugarHuda/neraca - neraca-psi.vercel.app"
Run "python -m pytest -q 2>&1 | Select-Object -Last 1"
At 212
Stamp
At 216
