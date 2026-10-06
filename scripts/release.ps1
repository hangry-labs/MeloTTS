param(
    [string]$DryRun = "0",
    [string]$NextVersion = "",
    [string]$SkipValidation = "0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-Enabled {
    param([string]$Value)
    return $Value -match '^(1|true|yes|y)$'
}

function Set-Text {
    param(
        [string]$Path,
        [string]$Text
    )
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($resolved, $Text, $encoding)
}

function Get-NextPatchSnapshot {
    param([string]$ReleaseVersion)
    if ($ReleaseVersion -notmatch '^v(\d+)\.(\d+)\.(\d+)$') {
        throw "Release version must look like v1.0.0. Got '$ReleaseVersion'."
    }
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3] + 1
    return "v$major.$minor.$patch-SNAPSHOT"
}

function Convert-ToPackageVersion {
    param([string]$DisplayVersion)
    return $DisplayVersion.TrimStart('v').Replace('-SNAPSHOT', '.dev0')
}

function Update-PackageVersion {
    param(
        [string]$Text,
        [string]$DisplayVersion
    )
    $packageVersion = Convert-ToPackageVersion $DisplayVersion
    $updated = [regex]::Replace(
        $Text,
        '(?m)^version = "[^"]+"$',
        "version = `"$packageVersion`"",
        1
    )
    if ($updated -eq $Text) {
        throw "Unable to update project.version in pyproject.toml."
    }
    return $updated
}

function Update-DockerImageTags {
    param(
        [string]$Text,
        [string]$ReleaseVersion
    )
    return [regex]::Replace(
        $Text,
        'hangrylabs/melotts:v\d+\.\d+\.\d+(_en)?(?:@sha256:[0-9a-f]{64})?',
        { param($match) "hangrylabs/melotts:$ReleaseVersion$($match.Groups[1].Value)" }
    )
}

function Invoke-Step {
    param(
        [string]$Description,
        [scriptblock]$Action
    )
    Write-Host "==> $Description"
    if (-not (Test-Enabled $DryRun)) {
        & $Action
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    if (-not (Test-Path -LiteralPath "VERSION")) {
        throw "VERSION file is missing from the repository root."
    }
    if (-not (Test-Path -LiteralPath "pyproject.toml")) {
        throw "pyproject.toml is missing from the repository root."
    }

    $snapshotVersion = (Get-Content -Raw -LiteralPath "VERSION").Trim()
    if ($snapshotVersion -notmatch '^v(\d+)\.(\d+)\.(\d+)-SNAPSHOT$') {
        throw "VERSION must be a snapshot such as v1.0.0-SNAPSHOT. Current: '$snapshotVersion'."
    }
    $releaseVersion = $snapshotVersion -replace '-SNAPSHOT$', ''

    if ([string]::IsNullOrWhiteSpace($NextVersion)) {
        $nextSnapshotVersion = Get-NextPatchSnapshot $releaseVersion
    } else {
        $nextSnapshotVersion = $NextVersion.Trim()
        if (-not $nextSnapshotVersion.StartsWith('v')) {
            $nextSnapshotVersion = "v$nextSnapshotVersion"
        }
        if (-not $nextSnapshotVersion.EndsWith('-SNAPSHOT')) {
            $nextSnapshotVersion = "$nextSnapshotVersion-SNAPSHOT"
        }
    }
    if ($nextSnapshotVersion -notmatch '^v\d+\.\d+\.\d+-SNAPSHOT$') {
        throw "NextVersion must look like v1.0.1-SNAPSHOT. Current: '$nextSnapshotVersion'."
    }

    $trackedPrivateFiles = @(git ls-files -- AGENTS.md .ai todo)
    if ($trackedPrivateFiles) {
        throw "Private agent files must not be tracked before release:`n$($trackedPrivateFiles -join "`n")"
    }

    $status = git status --porcelain -- . ':(exclude)todo' ':(exclude).ai'
    if ($status -and -not (Test-Enabled $DryRun)) {
        throw "Working tree outside .ai/ and todo/ must be clean before release. Commit or stash release-relevant changes first."
    }
    if (git rev-parse -q --verify "refs/tags/$releaseVersion" 2>$null) {
        throw "Tag $releaseVersion already exists."
    }

    Write-Host "Release version: $releaseVersion"
    Write-Host "Next snapshot:   $nextSnapshotVersion"

    Invoke-Step "Update release files for $releaseVersion" {
        Set-Text "VERSION" "$releaseVersion`n"
        $project = Get-Content -Raw -LiteralPath "pyproject.toml"
        Set-Text "pyproject.toml" (Update-PackageVersion $project $releaseVersion)

        $readme = Get-Content -Raw -LiteralPath "README.md"
        $readme = $readme.Replace("### $releaseVersion (in development)", "### $releaseVersion")
        $historyHeading = [regex]::Match($readme, '(?m)^## .*Version History\r?$')
        if (-not $historyHeading.Success) {
            throw "README.md is missing the version-history section."
        }
        $historyIndex = $historyHeading.Index
        $readmePrefix = Update-DockerImageTags $readme.Substring(0, $historyIndex) $releaseVersion
        Set-Text "README.md" ($readmePrefix + $readme.Substring($historyIndex))

        $dockerHub = Get-Content -Raw -LiteralPath "docs/dockerhub.md"
        Set-Text "docs/dockerhub.md" (Update-DockerImageTags $dockerHub $releaseVersion)
    }

    Invoke-Step "Run release validation" {
        if (-not (Test-Enabled $SkipValidation)) {
            task validate
            if ($LASTEXITCODE -ne 0) { throw "Project validation failed." }
            task image
            if ($LASTEXITCODE -ne 0) { throw "Full Docker image build failed." }
        }
    }

    Invoke-Step "Commit and tag $releaseVersion" {
        git add VERSION pyproject.toml README.md docs/dockerhub.md
        git commit -m "release: $releaseVersion"
        if ($LASTEXITCODE -ne 0) { throw "Release commit failed." }
        git tag -a $releaseVersion -m "Release $releaseVersion"
        if ($LASTEXITCODE -ne 0) { throw "Release tag failed." }
    }

    Invoke-Step "Prepare $nextSnapshotVersion" {
        Set-Text "VERSION" "$nextSnapshotVersion`n"
        $project = Get-Content -Raw -LiteralPath "pyproject.toml"
        Set-Text "pyproject.toml" (Update-PackageVersion $project $nextSnapshotVersion)
        git add VERSION pyproject.toml
        git commit -m "chore: start $nextSnapshotVersion"
        if ($LASTEXITCODE -ne 0) { throw "Next-snapshot commit failed." }
    }

    if (Test-Enabled $DryRun) {
        Write-Host "Dry run only: no files, builds, commits, or tags were changed."
    } else {
        Write-Host "Prepared $releaseVersion and $nextSnapshotVersion locally."
        Write-Host "Publish with: task releasepush RELEASE_VERSION=$releaseVersion"
    }
} finally {
    Pop-Location
}
