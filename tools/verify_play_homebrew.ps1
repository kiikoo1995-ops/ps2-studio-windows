param([ValidateSet('cubes_demo','console_demo')][string]$Demo = 'cubes_demo')
$ErrorActionPreference = 'Stop'

# A freely licensed homebrew PS2 demo (MIT). Never packaged with PS2 Studio.
$sourceCommit = '602441a6877a3136709d6320664340d52e3027a1'
$sourceBlob = if ($Demo -eq 'cubes_demo') { '27373da3d4fdf547d12910b6eb66db56598d0308' } else { 'fb916d10e7c6a1ce19c04dd86c8a8ad2ecd441ae' }
$expectedSize = if ($Demo -eq 'cubes_demo') { 243288 } else { 233856 }
New-Item -ItemType Directory -Force homebrew-test/$Demo | Out-Null
$folder = (Resolve-Path homebrew-test/$Demo).Path
$elf = Join-Path $folder "$Demo.elf"
$url = "https://raw.githubusercontent.com/glampert/ps2-homebrew/$sourceCommit/source/demos/bin/$Demo.elf"
Invoke-WebRequest -Uri $url -OutFile $elf
if ((Get-Item $elf).Length -ne $expectedSize) { throw 'Unexpected homebrew ELF size' }
$blob = (& git hash-object $elf).Trim()
if ($LASTEXITCODE -ne 0 -or $blob -ne $sourceBlob) { throw "Unexpected homebrew ELF: $blob" }
$header = [System.IO.File]::ReadAllBytes($elf)
if ($header[0] -ne 127 -or $header[1] -ne 69 -or $header[2] -ne 76 -or $header[3] -ne 70) {
  throw 'Homebrew file is not ELF'
}

$exe = (Resolve-Path engine/play/Play.exe).Path
$dir = Split-Path $exe
if (!(Test-Path (Join-Path $dir 'opengl32.dll'))) {
  throw 'App-local Mesa is required for hosted Windows tests'
}
$env:QT_OPENGL = 'desktop'
$env:PS2STUDIO_RENDERER = 'opengl'
$env:PS2STUDIO_RESOLUTION = '1'
$marker = Join-Path $folder 'elf-boot-confirmed.txt'
$statsFile = Join-Path $folder 'guest-stats.tsv'
$env:PS2STUDIO_CI_ELF_MARKER = $marker
$framePath = Join-Path $folder 'guest-frame.bmp'
$env:PS2STUDIO_CI_FRAME_PATH = $framePath
$env:PS2STUDIO_CI_STATS_FILE = $statsFile
$portable = Join-Path $dir 'portable.txt'
$portableData = Join-Path $dir 'Play Data Files'
New-Item -ItemType File -Path $portable -Force | Out-Null
$proc = $null
try {
  $proc = Start-Process -FilePath $exe -WorkingDirectory $dir -ArgumentList @('--elf', $elf) -PassThru
  Start-Sleep -Seconds 35
  $proc.Refresh()
  if ($proc.HasExited) { throw "Play terminated during homebrew: $($proc.ExitCode)" }
  if ($proc.MainWindowHandle -eq 0 -or !$proc.Responding) { throw 'Play window not responsive' }
  if (!(Test-Path $marker)) { throw 'ELF_BOOT_MARKER_MISSING: BootElf did not finish' }
  if ((Get-Content $marker -Raw).Trim() -ne 'BOOT_ELF_LOADED_AND_VM_RESUMED') {
    throw 'Unexpected ELF boot marker'
  }
  Write-Host 'HOMEBREW_ELF_BOOT_PASS: Play core loaded the original ELF and resumed VM'
  if (!(Test-Path $statsFile)) { throw 'GUEST_FPS_MISSING: no frame counters exported' }
  $samples = @()
  foreach ($line in @(Get-Content $statsFile)) {
    if ($line -match '^([0-9]+)\t([0-9]+)$') {
      $samples += [int]$Matches[1]
    }
  }
  $positive = @($samples | Where-Object { $_ -gt 0 })
  if ($positive.Count -lt 3) {
    throw "GUEST_FPS_ZERO_OR_STALLED: positive=$($positive.Count), all=$($samples.Count)"
  }
  $avgFps = [math]::Round(($positive | Measure-Object -Average).Average, 1)
  $minFps = ($positive | Measure-Object -Minimum).Minimum
  $maxFps = ($positive | Measure-Object -Maximum).Maximum
  $allAvg = [math]::Round(($samples | Measure-Object -Average).Average, 1)
  $zeroSamples = @($samples | Where-Object { $_ -eq 0 }).Count
  Write-Host "GUEST_FPS_MEASURED: positive_average=$avgFps positive_min=$minFps max=$maxFps all_average=$allAvg zero_samples=$zeroSamples total_samples=$($samples.Count) (hosted Windows CPU/Mesa)"
  $frameLog = $framePath + '.log'
  if (Test-Path $frameLog) { Get-Content -LiteralPath $frameLog | Select-Object -Last 20 | ForEach-Object { Write-Host $_ } }
  else { Write-Warning 'No GS presentation hook log: VM ticks alone do not establish rendered frames.' }
  $flipLog = $framePath + '.flips.tsv'
  if (Test-Path $flipLog) { Write-Host "GS_PRESENTATION_LOG_ROWS: $(@(Get-Content $flipLog).Count)" }
  if (!(Test-Path $framePath)) { throw 'GUEST_FRAME_MISSING: no pre-swap OpenGL framebuffer capture' }
  Add-Type -AssemblyName System.Drawing
  $bitmap = [System.Drawing.Bitmap]::new($framePath)
  try {
    if ($bitmap.Width -lt 128 -or $bitmap.Height -lt 128) {
      throw "GUEST_FRAME_INVALID_SIZE: $($bitmap.Width)x$($bitmap.Height)"
    }
    $sampleCount = 0
    $lit = 0
    $colours = New-Object 'System.Collections.Generic.HashSet[int]'
    for ($y = 0; $y -lt $bitmap.Height; $y += 12) {
      for ($x = 0; $x -lt $bitmap.Width; $x += 12) {
        $pixel = $bitmap.GetPixel($x, $y)
        $sampleCount++
        if (($pixel.R + $pixel.G + $pixel.B) -gt 75) { $lit++ }
        [void]$colours.Add($pixel.ToArgb())
      }
    }
    $percent = [math]::Round(100 * $lit / $sampleCount, 2)
    Write-Host "GUEST_FRAME_METRICS: $($bitmap.Width)x$($bitmap.Height), lit=$lit/$sampleCount ($percent%), colours=$($colours.Count)"
    if ($lit -lt [math]::Max(8, [int]($sampleCount * 0.004)) -or $colours.Count -lt 4) {
      throw 'GUEST_FRAME_BLACK_OR_STATIC'
    }
    Write-Host 'GUEST_FRAME_NONBLACK_PASS: genuine guest framebuffer from Play'
  } finally {
    $bitmap.Dispose()
  }
  Write-Host 'LIMITATION: GPU performance, input, audio and commercial game FPS remain unverified'
} finally {
  if ($proc -and !$proc.HasExited) { Stop-Process -Id $proc.Id -Force }
  Remove-Item -LiteralPath $portable -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $portableData -Recurse -Force -ErrorAction SilentlyContinue
}
