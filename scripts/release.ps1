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
    $versionPattern = [regex]::new(
        '(?m)^version = "[^"]+"$'
    )
    $updated = $versionPattern.Replace(
        $Text,
        "version = `"$packageVersion`"",
        1
    )
    if ($updated -eq $Text) {
        throw "Unable to update project.version in pyproject.toml."
    }
    return $updated
}

function Assert-PackageDocument {
    param(
        [string]$Text,
        [string]$DisplayVersion,
        [string]$Label
    )
    $expectedVersion = Convert-ToPackageVersion $DisplayVersion
    $versionMatches = [regex]::Matches($Text, '(?m)^version = "([^"]+)"$')
    if ($versionMatches.Count -ne 1) {
        throw "$Label must contain exactly one lowercase project.version assignment. Found $($versionMatches.Count)."
    }
    if ($versionMatches[0].Groups[1].Value -ne $expectedVersion) {
        throw "$Label project.version '$($versionMatches[0].Groups[1].Value)' does not match '$expectedVersion'."
    }
    if (-not [regex]::IsMatch($Text, '(?m)^VERSION = "VERSION"$')) {
        throw "$Label lost the wheel force-include mapping VERSION = `"VERSION`"."
    }
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

function Get-ReleaseReadme {
    param(
        [string]$Text,
        [string]$ReleaseVersion
    )
    $snapshotHeading = "### $ReleaseVersion (in development)"
    $stableHeading = "### $ReleaseVersion"
    if (-not $Text.Contains($snapshotHeading)) {
        throw "README.md must contain the exact release heading '$snapshotHeading'."
    }

    $snapshotIndex = $Text.IndexOf($snapshotHeading, [System.StringComparison]::Ordinal)
    $headingPattern = [regex]::new('(?m)^### ')
    $nextHeading = $headingPattern.Match(
        $Text,
        $snapshotIndex + $snapshotHeading.Length
    )
    $sectionEnd = if ($nextHeading.Success) { $nextHeading.Index } else { $Text.Length }
    $snapshotSection = $Text.Substring($snapshotIndex, $sectionEnd - $snapshotIndex)
    $releaseSection = $snapshotSection.Replace($snapshotHeading, $stableHeading)
    $releaseSection = $releaseSection.Replace(
        'The current development snapshot is published through the rolling tags from `main`:',
        'Run this release with either image variant:'
    )
    $releaseSection = $releaseSection.Replace(
        'hangrylabs/melotts:latest_en',
        "hangrylabs/melotts:$($ReleaseVersion)_en"
    )
    $releaseSection = $releaseSection.Replace(
        'hangrylabs/melotts:latest',
        "hangrylabs/melotts:$ReleaseVersion"
    )
    if ($releaseSection -eq $snapshotSection) {
        throw "README.md snapshot release section was not promoted."
    }

    $updated = $Text.Substring(0, $snapshotIndex) + $releaseSection + $Text.Substring($sectionEnd)
    $historyHeading = [regex]::Match($updated, '(?m)^## .*Version History\r?$')
    if (-not $historyHeading.Success) {
        throw "README.md is missing the version-history section."
    }
    $historyIndex = $historyHeading.Index
    $prefix = $updated.Substring(0, $historyIndex)
    $updatedPrefix = Update-DockerImageTags $prefix $ReleaseVersion
    if ($updatedPrefix -eq $prefix) {
        throw "README.md has no stable Docker image tag to promote."
    }
    return $updatedPrefix + $updated.Substring($historyIndex)
}

function Get-ReleaseDockerHub {
    param(
        [string]$Text,
        [string]$ReleaseVersion
    )
    $updated = Update-DockerImageTags $Text $ReleaseVersion
    if ($updated -eq $Text) {
        throw "docs/dockerhub.md has no release image tag to promote."
    }
    return $updated
}

function Get-NextSnapshotReadme {
    param(
        [string]$Text,
        [string]$ReleaseVersion,
        [string]$NextSnapshotVersion
    )
    $nextVersion = $NextSnapshotVersion -replace '-SNAPSHOT$', ''
    $nextHeading = "### $nextVersion (in development)"
    if ($Text.Contains($nextHeading)) {
        throw "README.md already contains the next snapshot heading '$nextHeading'."
    }

    $stableHeading = [regex]::Match(
        $Text,
        "(?m)^### $([regex]::Escape($ReleaseVersion))\r?$"
    )
    if (-not $stableHeading.Success) {
        throw "README.md is missing the promoted release heading '### $ReleaseVersion'."
    }
    $lineEnding = if ($Text.Contains("`r`n")) { "`r`n" } else { "`n" }
    $snapshotBlock = @(
        $nextHeading,
        '',
        'The current development snapshot is published through the rolling tags from `main`:',
        '',
        '**Full image**',
        '',
        '```bash',
        'docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest',
        '```',
        '',
        '**English-family image**',
        '',
        '```bash',
        'docker run --rm -p 8888:8888 --gpus all -v melotts_data:/app/persistent hangrylabs/melotts:latest_en',
        '```',
        '',
        ''
    ) -join $lineEnding
    return $Text.Insert($stableHeading.Index, $snapshotBlock)
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

    $snapshotVersion = (Get-Content -Raw -Encoding utf8 -LiteralPath "VERSION").Trim()
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

    $trackedPrivateFiles = @(git ls-files -- AGENTS.md .ai)
    if ($trackedPrivateFiles) {
        throw "Private agent files must not be tracked before release:`n$($trackedPrivateFiles -join "`n")"
    }

    $branch = (git branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to determine the current Git branch."
    }
    if ($branch -ne "main") {
        throw "Releases must run from main. Current branch: '$branch'."
    }

    $status = git status --porcelain --untracked-files=all -- . ':(exclude).ai' ':(exclude).ai/**'
    if ($status) {
        if (Test-Enabled $DryRun) {
            Write-Warning "The real release requires a clean working tree outside .ai/."
            $status | ForEach-Object { Write-Host "  $_" }
        } else {
            throw "Working tree outside .ai/ must be clean before release. Commit or stash release-relevant changes first.`n$($status -join "`n")"
        }
    }
    if (git rev-parse -q --verify "refs/tags/$releaseVersion" 2>$null) {
        throw "Tag $releaseVersion already exists."
    }

    $projectSource = Get-Content -Raw -Encoding utf8 -LiteralPath "pyproject.toml"
    $expectedProjectVersion = Convert-ToPackageVersion $snapshotVersion
    $projectVersionMatch = [regex]::Match($projectSource, '(?m)^version = "([^"]+)"$')
    if (-not $projectVersionMatch.Success) {
        throw "Unable to read project.version from pyproject.toml."
    }
    if ($projectVersionMatch.Groups[1].Value -ne $expectedProjectVersion) {
        throw "pyproject.toml version '$($projectVersionMatch.Groups[1].Value)' does not match VERSION '$snapshotVersion' (expected '$expectedProjectVersion')."
    }

    $readmeSource = Get-Content -Raw -Encoding utf8 -LiteralPath "README.md"
    $dockerHubSource = Get-Content -Raw -Encoding utf8 -LiteralPath "docs/dockerhub.md"
    $releaseProject = Update-PackageVersion $projectSource $releaseVersion
    $releaseReadme = Get-ReleaseReadme $readmeSource $releaseVersion
    $releaseDockerHub = Get-ReleaseDockerHub $dockerHubSource $releaseVersion
    $nextProject = Update-PackageVersion $releaseProject $nextSnapshotVersion
    $nextReadme = Get-NextSnapshotReadme $releaseReadme $releaseVersion $nextSnapshotVersion
    Assert-PackageDocument $releaseProject $releaseVersion "Release pyproject.toml"
    Assert-PackageDocument $nextProject $nextSnapshotVersion "Next-snapshot pyproject.toml"

    Write-Host "Release version: $releaseVersion"
    Write-Host "Next snapshot:   $nextSnapshotVersion"
    Write-Host "Document transitions validated in memory."

    Invoke-Step "Update release files for $releaseVersion" {
        Set-Text "VERSION" "$releaseVersion`n"
        Set-Text "pyproject.toml" $releaseProject
        Set-Text "README.md" $releaseReadme
        Set-Text "docs/dockerhub.md" $releaseDockerHub
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
        Set-Text "pyproject.toml" $nextProject
        Set-Text "README.md" $nextReadme
        git add VERSION pyproject.toml README.md
        git commit -m "chore: start $nextSnapshotVersion"
        if ($LASTEXITCODE -ne 0) { throw "Next-snapshot commit failed." }
    }

    if (Test-Enabled $DryRun) {
        Write-Host "Dry run only: release and next-snapshot transforms were validated; no files, builds, commits, or tags were changed."
    } else {
        Write-Host "Prepared $releaseVersion and $nextSnapshotVersion locally."
        Write-Host "Publish with: task releasepush RELEASE_VERSION=$releaseVersion"
        Write-Host "After both image variants publish, pin their top-level OCI digests in README.md and docs/dockerhub.md."
    }
} finally {
    Pop-Location
}
