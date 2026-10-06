param(
    [string]$BaseUrl = "http://localhost:8888",
    [switch]$Play,
    [string]$ExampleName = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent
$examplesPath = [IO.Path]::GetFullPath((Join-Path $repoRoot "examples"))

function Assert-ExamplesPath {
    param([string]$Path)

    $resolved = [IO.Path]::GetFullPath($Path)
    $prefix = $examplesPath.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to write outside the examples directory: $resolved"
    }
    return $resolved
}

function Expand-UnicodeEscapes {
    param([string]$Value)

    return [Text.RegularExpressions.Regex]::Unescape($Value)
}

$multilingualCafeSsml = Expand-UnicodeEscapes @"
<speak>
  <voice name="EN-Newest"><prosody speed="0.96" pitch="+0.5st">Welcome! Is this seat free?</prosody></voice>
  <break time="180ms"/>
  <voice name="ES"><prosody speed="0.94">S\u00ed, adelante. Estamos probando una conversaci\u00f3n multiling\u00fce.</prosody></voice>
  <break time="180ms"/>
  <voice name="FR"><prosody speed="0.95" pitch="+0.5st">Parfait ! Chaque phrase utilise son propre mod\u00e8le vocal.</prosody></voice>
  <break time="180ms"/>
  <voice name="EN-Newest"><prosody tempo="1.03">And the finished dialogue arrives as one audio file.</prosody></voice>
</speak>
"@

$eastAsiaSsml = Expand-UnicodeEscapes @"
<speak>
  <voice name="ZH"><prosody speed="0.95">\u5927\u5bb6\u597d\uff0c\u4eca\u5929\u7684\u8bed\u97f3\u6d4b\u8bd5\u51c6\u5907\u597d\u4e86\u5417\uff1f</prosody></voice>
  <break time="180ms"/>
  <voice name="JP"><prosody speed="0.96">\u306f\u3044\u3001\u6e96\u5099\u3067\u304d\u307e\u3057\u305f\u3002\u97f3\u58f0\u306f\u3068\u3066\u3082\u81ea\u7136\u3067\u3059\u3002</prosody></voice>
  <break time="180ms"/>
  <voice name="KR"><prosody speed="0.94">\ub124, \uc800\ub3c4 \uc900\ube44\ub410\uc5b4\uc694. \uc138 \uac00\uc9c0 \uc5b8\uc5b4\ub97c \ud55c \ud30c\uc77c\uc5d0 \ub2f4\uc544 \ubd05\uc2dc\ub2e4.</prosody></voice>
  <break time="180ms"/>
  <voice name="EN-Newest"><prosody tempo="1.03">Perfect. The international check-in is complete.</prosody></voice>
</speak>
"@

$examples = @(
    @{
        Name = "Studio readiness"
        File = "melotts-ssml-studio-dialogue.mp3"
        Language = "EN"
        Speaker = "EN-BR"
        Languages = "EN"
        Speakers = "EN-BR,EN-US"
        MinimumDuration = 11.0
        Ssml = @"
<speak>
  <voice name="EN-BR"><prosody speed="0.96" pitch="+0.5st">Good morning. Is the speech service ready for today's demonstration?</prosody></voice>
  <break time="180ms"/>
  <voice name="EN-US"><prosody speed="0.92" pitch="-1st">Ready and listening. I warmed every language model before you arrived.</prosody></voice>
  <break time="180ms"/>
  <voice name="EN-BR"><prosody tempo="1.04" pitch="+1st">Every model? That sounds rather ambitious.</prosody></voice>
  <break time="180ms"/>
  <voice name="EN-US"><prosody speed="0.9" volume="0.96">Perhaps. But nobody enjoys waiting for the first sentence.</prosody></voice>
</speak>
"@
    }
    @{
        Name = "English accent roundtable"
        File = "melotts-ssml-accent-roundtable.mp3"
        Language = "EN"
        Speaker = "EN-BR"
        Languages = "EN"
        Speakers = "EN-BR,EN-US,EN-AU,EN_INDIA"
        MinimumDuration = 10.0
        Ssml = @"
<speak>
  <voice name="EN-BR"><prosody speed="0.96">Shall we compare notes before the launch?</prosody></voice>
  <break time="150ms"/>
  <voice name="EN-US"><prosody speed="1.02" pitch="+0.5st">Absolutely. The application interface is ready, and the audio sounds clear.</prosody></voice>
  <break time="150ms"/>
  <voice name="EN-AU"><prosody tempo="1.04">Brilliant. I have checked the container twice.</prosody></voice>
  <break time="150ms"/>
  <voice name="EN_INDIA"><prosody speed="0.94" pitch="-0.5st">Then we agree. One service, four English voices, and no extra setup.</prosody></voice>
</speak>
"@
    }
    @{
        Name = "Multilingual cafe"
        File = "melotts-ssml-multilingual-cafe.mp3"
        Language = "EN_NEWEST"
        Speaker = "EN-Newest"
        Languages = "EN_NEWEST,ES,FR"
        Speakers = "EN-Newest,ES,FR"
        MinimumDuration = 10.0
        Ssml = $multilingualCafeSsml
    }
    @{
        Name = "East Asia check-in"
        File = "melotts-ssml-east-asia.mp3"
        Language = "ZH"
        Speaker = "ZH"
        Languages = "ZH,JP,KR,EN_NEWEST"
        Speakers = "ZH,JP,KR,EN-Newest"
        MinimumDuration = 8.0
        Ssml = $eastAsiaSsml
    }
    @{
        Name = "Directed delivery"
        File = "melotts-ssml-directed-delivery.mp3"
        Language = "EN_NEWEST"
        Speaker = "EN-Newest"
        Languages = "EN_NEWEST"
        Speakers = "EN-Newest"
        MinimumDuration = 10.0
        Ssml = @"
<speak>
  <voice name="EN-Newest">
    <prosody speed="1.04" pitch="+2st">For the next take, say <sub alias="Hangry Labs">H L</sub>, then read ticket <say-as interpret-as="number">314</say-as>.</prosody>
    <break time="350ms"/>
    <prosody speed="0.9" pitch="-1.5st">Understood. Ticket <say-as interpret-as="number">314</say-as> is the <say-as interpret-as="ordinal">3</say-as> item in the queue.</prosody>
    <break time="500ms"/>
    <prosody tempo="1.06" volume="0.94">Export <say-as interpret-as="characters">MP3</say-as>, pause, and deliver the final line.</prosody>
    <break time="700ms"/>
    <prosody speed="0.86" pitch="-0.5st">The recording is ready.</prosody>
  </voice>
</speak>
"@
    }
)

if ($ExampleName) {
    $examples = @($examples | Where-Object { $_.Name -eq $ExampleName })
    if ($examples.Count -eq 0) {
        throw "Unknown SSML example: $ExampleName"
    }
}

Invoke-RestMethod -Uri "$BaseUrl/tts/ping" | Out-Null

foreach ($example in $examples) {
    $outputPath = Assert-ExamplesPath (Join-Path $examplesPath $example.File)
    $pendingPath = Assert-ExamplesPath "$outputPath.pending"
    $body = @{
        text = $example.Ssml
        input_type = "ssml"
        language = $example.Language
        speaker_id = $example.Speaker
        sdp_ratio = 0.0
        noise_scale = 0.4
        noise_scale_w = 0.0
        format = "mp3"
    } | ConvertTo-Json -Compress
    $completed = $false
    $lastError = "generation did not run"

    try {
        foreach ($attempt in 1..3) {
            Remove-Item -LiteralPath $pendingPath -Force -ErrorAction SilentlyContinue
            try {
                $response = Invoke-WebRequest `
                    -UseBasicParsing `
                    -Method Post `
                    -Uri "$BaseUrl/tts/generate" `
                    -ContentType "application/json; charset=utf-8" `
                    -Body ([Text.Encoding]::UTF8.GetBytes($body)) `
                    -OutFile $pendingPath `
                    -PassThru

                $languages = $response.Headers["X-MeloTTS-Language"] -join ","
                $speakers = $response.Headers["X-MeloTTS-Speaker"] -join ","
                $inputType = $response.Headers["X-MeloTTS-Input-Type"] -join ""
                $duration = [double]::Parse(
                    ($response.Headers["X-MeloTTS-Duration"] -join ""),
                    [Globalization.CultureInfo]::InvariantCulture
                )
                $size = (Get-Item -LiteralPath $pendingPath).Length

                if ($inputType -ne "ssml") {
                    throw "unexpected input type: $inputType"
                }
                if ($languages -ne $example.Languages) {
                    throw "unexpected languages: $languages"
                }
                if ($speakers -ne $example.Speakers) {
                    throw "unexpected speakers: $speakers"
                }
                if ($size -le 10KB) {
                    throw "unexpectedly small output: $size bytes"
                }
                if ($duration -lt $example.MinimumDuration) {
                    throw "unexpectedly short output: $duration seconds"
                }

                Move-Item -LiteralPath $pendingPath -Destination $outputPath -Force
                $completed = $true
                break
            }
            catch {
                $lastError = $_.Exception.Message
                if ($attempt -lt 3) {
                    Write-Warning "$($example.Name) attempt $attempt failed validation: $lastError. Retrying."
                    Start-Sleep -Seconds 2
                }
            }
        }
    }
    finally {
        Remove-Item -LiteralPath $pendingPath -Force -ErrorAction SilentlyContinue
    }

    if (-not $completed) {
        throw "$($example.Name) failed after three attempts: $lastError"
    }

    Write-Output "$($example.Name): $speakers; $languages; $duration seconds; $size bytes"
    if ($Play) {
        Start-Process -FilePath $outputPath
    }
}
