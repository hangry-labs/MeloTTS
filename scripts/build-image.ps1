param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("FULL", "EN_ONLY")]
    [string]$Profile,

    [Parameter(Mandatory = $true)]
    [string]$Image
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$buildDate = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
$vcsRef = (git -C $repoRoot rev-parse --short=12 HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($vcsRef)) {
    throw "Unable to resolve the current Git revision."
}

$appVersion = (Get-Content -Raw -LiteralPath (Join-Path $repoRoot "VERSION")).Trim()
if ([string]::IsNullOrWhiteSpace($appVersion)) {
    throw "VERSION must not be empty."
}

$languages = if ($Profile -eq "FULL") {
    "EN,EN_V2,EN_NEWEST,ES,FR,ZH,JP,KR"
} else {
    "EN,EN_V2,EN_NEWEST"
}
$buildId = "$buildDate@$vcsRef"

Write-Host "Building $Image ($Profile) at $buildDate from $vcsRef"
& docker build `
    --build-arg "APP_VERSION=$appVersion" `
    --build-arg "BUILD_DATE=$buildDate" `
    --build-arg "BUILD_ID=$buildId" `
    --build-arg "VCS_REF=$vcsRef" `
    --build-arg "INIT_DOWNLOADS_PROFILE=$Profile" `
    --build-arg "INIT_DOWNLOADS_STRICT=1" `
    --build-arg "DEFAULT_TTS_LANGUAGES=$languages" `
    -t $Image `
    $repoRoot

if ($LASTEXITCODE -ne 0) {
    throw "Docker build failed with exit code $LASTEXITCODE."
}
