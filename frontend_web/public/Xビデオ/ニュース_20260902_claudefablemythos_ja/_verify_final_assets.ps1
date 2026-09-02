[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference = 'Stop'

$project = 'ニュース_20260902_claudefablemythos_ja'
$base = if ($PSScriptRoot) { $PSScriptRoot } else { Join-Path (Get-Location) 'frontend_web/public/Xビデオ/ニュース_20260902_claudefablemythos_ja' }
$scenarioPath = Join-Path $base 'scenario.js'
$indexPath = Join-Path $base 'index.html'
$audioScriptPath = Join-Path $base '_gen_dialogue_audio.py'
$imageScriptPath = Join-Path $base '_gen_scene_images.py'
$errors = [System.Collections.Generic.List[string]]::new()
$notes = [System.Collections.Generic.List[string]]::new()

function Require-Condition([bool]$condition, [string]$message) {
  if ($condition) { $notes.Add("OK: $message") } else { $errors.Add("NG: $message") }
}

Require-Condition (Test-Path -LiteralPath $scenarioPath -PathType Leaf) 'scenario.js が存在する'
if (Test-Path -LiteralPath $scenarioPath -PathType Leaf) {
  $scenarioRaw = Get-Content -Raw -Encoding UTF8 -LiteralPath $scenarioPath
  Require-Condition ($scenarioRaw -match 'window\.SCENARIO') "scenario.js に window.SCENARIO がある"
  Require-Condition ($scenarioRaw -match '"id"\s*:\s*"scene_999"') "scenario.js に scene_999 がある"
  try {
    $json = ($scenarioRaw -replace '^\s*window\.SCENARIO\s*=\s*', '' -replace ';\s*$', '') | ConvertFrom-Json
    Require-Condition ($json.project_name -eq $project) "scenario.js の project_name が $project"
    Require-Condition ($json.language -eq 'ja') 'scenario.js の language が ja'
    $scene000 = @($json.scenes | Where-Object { $_.id -eq 'scene_000' })[0]
    $firstFemale = @($scene000.dialogue | Where-Object { $_.speaker -eq 'female' })[0]
    $introText = "$($firstFemale.telop_text) $($firstFemale.naration_text)"
    Require-Condition ($introText -match 'AiDiy' -and $introText -match 'ビデオ.*生成') 'scene_000 の最初の female 発話に AiDiy のビデオページ生成機能の明記がある'

    $referencedImages = @($json.scenes | ForEach-Object { $_.image } | Where-Object { $_ })
    $referencedAudio = @($json.scenes | ForEach-Object { $_.dialogue } | ForEach-Object { $_.audio } | Where-Object { $_ })
    $dialogues = @($json.scenes | ForEach-Object { $_.dialogue })
    Require-Condition ($dialogues.Count -eq $referencedAudio.Count) '全発話に音声ファイル指定がある'
    foreach ($dialogue in $dialogues) {
      $telop = [string]$dialogue.telop_text
      $narration = [string]$dialogue.naration_text
      Require-Condition ($telop -match '[ぁ-んァ-ン一-龯]') "字幕が日本語で空でない: $($dialogue.audio)"
      Require-Condition ($narration -match '[ぁ-んァ-ン一-龯]') "ナレーション原稿が日本語で空でない: $($dialogue.audio)"
    }
  } catch {
    $errors.Add("NG: scenario.js を JSON として解釈できません: $($_.Exception.Message)")
  }
}

$images = @(Get-ChildItem -LiteralPath (Join-Path $base 'images') -Filter '*.png' -File -ErrorAction SilentlyContinue)
Require-Condition ($images.Count -ge 7) "images に PNG が 7 枚以上ある（$($images.Count) 枚）"
foreach ($image in $images) {
  $header = [System.IO.File]::ReadAllBytes($image.FullName) | Select-Object -First 8
  $pngHeader = [byte[]](137,80,78,71,13,10,26,10)
  Require-Condition (($header.Count -eq 8) -and -not (Compare-Object $header $pngHeader)) "PNG ヘッダーが正常: $($image.Name)"
}
if ($referencedImages) {
  foreach ($relativePath in $referencedImages) {
    Require-Condition (Test-Path -LiteralPath (Join-Path $base $relativePath) -PathType Leaf) "scenario.js が参照する画像が存在する: $relativePath"
  }
}

$audios = @(Get-ChildItem -LiteralPath (Join-Path $base 'audio') -Filter '*.mp3' -File -ErrorAction SilentlyContinue)
Require-Condition ($audios.Count -ge 28) "audio に MP3 が 28 本以上ある（$($audios.Count) 本）"
foreach ($audio in $audios) {
  Require-Condition ($audio.Length -gt 500) "MP3 が空・生成途中でない: $($audio.Name)"
}
if ($referencedAudio) {
  foreach ($relativePath in $referencedAudio) {
    Require-Condition (Test-Path -LiteralPath (Join-Path $base $relativePath) -PathType Leaf) "scenario.js が参照する音声が存在する: $relativePath"
  }
}

$ffprobe = Get-Command ffprobe -ErrorAction SilentlyContinue
if ($ffprobe) {
  $audioDurations = @{}
  foreach ($audio in $audios) {
    $duration = & $ffprobe.Source -v error -show_entries format=duration -of default=nokey=1:noprint_wrappers=1 $audio.FullName 2>$null
    $durationValue = 0.0
    $readable = [double]::TryParse("$duration", [ref]$durationValue) -and $durationValue -gt 0
    Require-Condition $readable "MP3 を ffprobe で読める: $($audio.Name)"
    if ($readable) { $audioDurations[('audio/' + $audio.Name)] = $durationValue }
  }
  if ($json) {
    $totalDuration = 0.0
    foreach ($scene in $json.scenes) {
      $sceneDuration = 0.0
      foreach ($dialogue in $scene.dialogue) {
        $actual = $audioDurations[$dialogue.audio]
        $sceneDuration += $actual
        Require-Condition ([math]::Abs($actual - [double]$dialogue.duration_sec) -le 0.1) "音声実尺と scenario.js の尺が一致: $($dialogue.audio)"
      }
      $totalDuration += $sceneDuration
      Require-Condition ([math]::Abs($sceneDuration - [double]$scene.duration_sec) -le 0.1) "シーン尺が音声合計と一致: $($scene.id)"
    }
    Require-Condition ([math]::Abs($totalDuration - [double]$json.total_duration_sec) -le 0.1) 'total_duration_sec が全音声の合計尺と一致'
  }
} else {
  $notes.Add('INFO: ffprobe が見つからないため、MP3 のデコード検証は省略しました。')
}

Require-Condition (Test-Path -LiteralPath $indexPath -PathType Leaf) 'index.html が存在する'
if (Test-Path -LiteralPath $indexPath -PathType Leaf) {
  $indexRaw = Get-Content -Raw -Encoding UTF8 -LiteralPath $indexPath
  Require-Condition ($indexRaw.Contains($project)) "index.html に今回のフォルダ名 $project がある"
  Require-Condition ($indexRaw -match '<html\s+lang="ja"') 'index.html の表示言語が ja'
}

Require-Condition (Test-Path -LiteralPath $audioScriptPath -PathType Leaf) '_gen_dialogue_audio.py が存在する'
if (Test-Path -LiteralPath $audioScriptPath -PathType Leaf) {
  $audioScriptRaw = Get-Content -Raw -Encoding UTF8 -LiteralPath $audioScriptPath
  Require-Condition ($audioScriptRaw -match "TTS_LANGUAGE\s*=\s*'ja'") '_gen_dialogue_audio.py の音声合成言語が ja'
  Require-Condition ($audioScriptRaw.Contains($project)) '_gen_dialogue_audio.py の出力先が今回のフォルダを指す'
}
Require-Condition (Test-Path -LiteralPath $imageScriptPath -PathType Leaf) '_gen_scene_images.py が存在する'
if (Test-Path -LiteralPath $imageScriptPath -PathType Leaf) {
  $imageScriptRaw = Get-Content -Raw -Encoding UTF8 -LiteralPath $imageScriptPath
  Require-Condition ($imageScriptRaw.Contains($project)) '_gen_scene_images.py の出力先が今回のフォルダを指す'
  Require-Condition ($imageScriptRaw -match 'Japanese technology news video') '_gen_scene_images.py が日本語ニュース向け画像を指定している'
}

$notes | ForEach-Object { $_ }
if ($errors.Count) {
  $errors | ForEach-Object { $_ }
  exit 1
}
Write-Output 'RESULT: OK（最終素材検証に合格）'
