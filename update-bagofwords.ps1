param(
    [string]$ImageName = "kashika-ai"
)

$ErrorActionPreference = "Stop"

function Info { param([string]$Message) Write-Host "[INFO]  $Message" -ForegroundColor Cyan }
function Ok   { param([string]$Message) Write-Host "[OK]    $Message" -ForegroundColor Green }
function Err  { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

try {
    $repoRoot = (& git rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $repoRoot) {
        throw "Run this script from inside the KashikaAI Git repository."
    }
    $repoRoot = $repoRoot.Trim()
    Set-Location $repoRoot

    $dockerfilePath = Join-Path $repoRoot "Dockerfile"
    $versionPath = Join-Path $repoRoot "VERSION"

    if (-not (Test-Path -LiteralPath $dockerfilePath)) {
        throw "Dockerfile not found."
    }
    if (-not (Test-Path -LiteralPath $versionPath)) {
        throw "VERSION file not found."
    }

    $version = (Get-Content -LiteralPath $versionPath -Raw).Trim()
    if (-not $version) {
        throw "VERSION file is empty."
    }

    Info "Building project version $version"

    $originalText = [System.IO.File]::ReadAllText(
        $dockerfilePath,
        [System.Text.Encoding]::UTF8
    )
    $newline = if ($originalText.Contains("`r`n")) { "`r`n" } else { "`n" }
    $hadTrailingNewline = $originalText.EndsWith("`n")

    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($line in [System.IO.File]::ReadAllLines(
        $dockerfilePath,
        [System.Text.Encoding]::UTF8
    )) {
        [void]$lines.Add($line)
    }

    $aptSourceFix = "sed -i 's|http://archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g; s|http://security.ubuntu.com/ubuntu|https://security.ubuntu.com/ubuntu|g' /etc/apt/sources.list.d/ubuntu.sources"
    $insertions = 0

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]

        if ($line -match '^(?<indent>\s*)RUN apt-get update && \\\s*$') {
            $indent = $Matches["indent"]
            $lines[$i] = "${indent}RUN $aptSourceFix && \"
            $lines.Insert($i + 1, "${indent}    apt-get update && \")
            $i++
            $insertions++
            continue
        }

        if ($line -match '^(?<indent>\s*)apt-get update && \\\s*$') {
            if ($i -gt 0 -and $lines[$i - 1].Contains("ubuntu.sources")) {
                continue
            }

            $indent = $Matches["indent"]
            $lines.Insert($i, "${indent}$aptSourceFix && \")
            $i++
            $insertions++
        }
    }

    if ($insertions -gt 0) {
        $newText = [string]::Join($newline, $lines)
        if ($hadTrailingNewline) {
            $newText += $newline
        }

        $backupPath = Join-Path $env:TEMP (
            "KashikaAI-Dockerfile-before-https-{0}.bak" -f (Get-Date -Format "yyyyMMdd-HHmmss")
        )
        Copy-Item -LiteralPath $dockerfilePath -Destination $backupPath
        [System.IO.File]::WriteAllText(
            $dockerfilePath,
            $newText,
            (New-Object System.Text.UTF8Encoding($false))
        )

        Ok "Updated Dockerfile package sources to HTTPS."
        Info "Backup saved to: $backupPath"
    } else {
        Info "Dockerfile already has the HTTPS fix."
    }

    $imageTag = "${ImageName}:v${version}"
    Info "Building Docker image $imageTag ..."
    & docker build -t $imageTag .
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed. Review the Docker output above."
    }

    & docker tag $imageTag "${ImageName}:latest"
    if ($LASTEXITCODE -ne 0) {
        throw "Image built, but tagging it as latest failed."
    }

    Ok "Built $imageTag and ${ImageName}:latest"
}
catch {
    Err $_.Exception.Message
    exit 1
}