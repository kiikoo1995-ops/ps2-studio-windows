# Compare requested 1x/2x/4x/8x OpenGL profiles on a native Windows GPU.
# PowerShell 7 + Python. Run against an extracted experimental package.
param([Parameter(Mandatory=$true)][string]$PackageRoot,
      [string]$Output = 'play-benchmark',
      [ValidateRange(20,120)][int]$Seconds = 30)
$ErrorActionPreference = 'Stop'
$source = Join-Path (Resolve-Path $PackageRoot).Path 'engine/play'
if (!(Test-Path (Join-Path $source 'Play.exe'))) { throw 'Native engine missing' }
if (Test-Path (Join-Path $source 'opengl32.dll')) { throw 'Software GL override found' }
if (!(Test-Path (Join-Path $source 'ps2studio-profile-v1.txt'))) { throw 'Profile hook missing' }
New-Item -ItemType Directory -Force $Output | Out-Null
$out = (Resolve-Path $Output).Path
$demo = Join-Path $out 'cubes_demo.elf'
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/glampert/ps2-homebrew/602441a6877a3136709d6320664340d52e3027a1/source/demos/bin/cubes_demo.elf' -OutFile $demo
$bytes = [IO.File]::ReadAllBytes($demo)
$prefix = [Text.Encoding]::ASCII.GetBytes("blob $($bytes.Length)" + [char]0)
$sha = [Security.Cryptography.SHA1]::Create()
try { $blob = [Convert]::ToHexString($sha.ComputeHash([byte[]]($prefix + $bytes))).ToLowerInvariant() }
finally { $sha.Dispose() }
if ($bytes.Length -ne 243288 -or $blob -ne '27373da3d4fdf547d12910b6eb66db56598d0308') { throw 'Unexpected homebrew bytes' }
$reports = @()
foreach ($scale in @(1,2,4,8)) {
  $case = Join-Path $out ("opengl-" + $scale + "x")
  if (Test-Path $case) { throw "Output already exists: $case" }
  $scratch = Join-Path ([IO.Path]::GetTempPath()) ("ps2studio-bench-" + [guid]::NewGuid())
  New-Item -ItemType Directory -Force $scratch,$case | Out-Null
  $process = $null
  $result = [ordered]@{requested_scale=$scale; renderer='opengl'; status='failed'; actual_scale_verified=$false; actual_gpu_verified=$false}
  try {
    Get-ChildItem -LiteralPath $source -Force | Where-Object {$_.Name -notin @('Play Data Files','portable.txt')} |
      Copy-Item -Destination $scratch -Recurse -Force
    New-Item -ItemType File -Path (Join-Path $scratch 'portable.txt') | Out-Null
    $env:QT_OPENGL = 'desktop'
    $env:PS2STUDIO_RENDERER = 'opengl'
    $env:PS2STUDIO_RESOLUTION = [string]$scale
    $env:PS2STUDIO_CI_ELF_MARKER = Join-Path $case 'elf-boot-confirmed.txt'
    $env:PS2STUDIO_CI_STATS_FILE = Join-Path $case 'guest-stats.tsv'
    $env:PS2STUDIO_CI_FRAME_PATH = Join-Path $case 'guest-frame.bmp'
    $process = Start-Process -FilePath (Join-Path $scratch 'Play.exe') -WorkingDirectory $scratch -ArgumentList @('--elf', ('"' + $demo + '"')) -PassThru
    Start-Sleep -Seconds $Seconds
    $process.Refresh()
    if ($process.HasExited) { throw "Play exit $($process.ExitCode)" }
    if (!$process.Responding -or $process.MainWindowHandle -eq 0) { throw 'Play window unresponsive' }
    if (!(Test-Path $env:PS2STUDIO_CI_ELF_MARKER) -or (Get-Content $env:PS2STUDIO_CI_ELF_MARKER -Raw).Trim() -ne 'BOOT_ELF_LOADED_AND_VM_RESUMED') { throw 'Boot marker missing' }
    if (!(Test-Path $env:PS2STUDIO_CI_FRAME_PATH)) { throw 'Framebuffer capture missing' }
    $summary = & python (Join-Path $PSScriptRoot 'analyze_play_stats.py') $env:PS2STUDIO_CI_STATS_FILE --warmup 3
    if ($LASTEXITCODE -ne 0) { throw 'Counter analysis failed' }
    $result['counter_summary'] = (($summary -join [Environment]::NewLine) | ConvertFrom-Json)
    if ($result['counter_summary'].max_frames_per_interval -le 0) { throw 'No guest frames' }
    $result['status'] = 'boot_and_counters_verified_capture_present'
    $result['limitations'] = 'Requested scale only. Verify actual GPU, internal resolution, pixels and per-frame timing separately.'
  } catch {
    $result['error'] = $_.Exception.Message
  } finally {
    if ($process -and !$process.HasExited) { Stop-Process -Id $process.Id -Force }
    Remove-Item -LiteralPath $scratch -Recurse -Force -ErrorAction SilentlyContinue
    foreach ($key in @('PS2STUDIO_RENDERER','PS2STUDIO_RESOLUTION','PS2STUDIO_CI_ELF_MARKER','PS2STUDIO_CI_STATS_FILE','PS2STUDIO_CI_FRAME_PATH')) {
      Remove-Item "Env:$key" -ErrorAction SilentlyContinue
    }
  }
  $result | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 (Join-Path $case 'result.json')
  $reports += [pscustomobject]$result
}
$reports | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 (Join-Path $out 'summary.json')
$reports | Format-Table requested_scale,status,error
if (@($reports | Where-Object status -eq 'failed').Count -gt 0) { exit 1 }
