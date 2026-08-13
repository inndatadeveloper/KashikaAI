# ============================================================
#  update-bagofwords.ps1
#  Usage: .\update-bagofwords.ps1
#         .\update-bagofwords.ps1 -ImageName "my-image"
# ============================================================

param(
    [string]$ImageName = "kashika-ai"
)

$ErrorActionPreference = "Stop"

function Info { param($msg) Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Ok   { param($msg) Write-Host "[OK]    $msg" -ForegroundColor Green }
function Warn { param($msg) Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Err  { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

function Fix-LineEndings {
    param([string]$FilePath)
    # IMPORTANT: without an explicit encoding, .NET's ReadAllText only
    # auto-detects UTF-8 via a BOM. Shell scripts from git have no BOM, so
    # it silently falls back to the system ANSI codepage and mangles any
    # multi-byte UTF-8 characters (emoji, box-drawing chars, etc.) in the
    # file. Forcing UTF-8 (no BOM) on both read and write avoids that.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $raw = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)
    $fixed = $raw -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($FilePath, $fixed, $utf8NoBom)
    Ok "Fixed line endings: $FilePath"
}

function Has-ConflictMarkers {
    param([string]$FilePath)
    $lines = [System.IO.File]::ReadAllLines($FilePath)
    foreach ($line in $lines) {
        if ($line.StartsWith("<<<<<<") -or $line.StartsWith("======") -or $line.StartsWith(">>>>>>")) {
            return $true
        }
    }
    return $false
}

# ── 0. Check directory ──────────────────────────────────────
if (-not (Test-Path ".\Dockerfile")) {
    Err "Run this script from your bagofwords root directory."
    exit 1
}

Info "=== bagofwords Update Script ==="
Info "Working directory: $PWD"

# ── 1. Read current version ─────────────────────────────────
$currentVersion = "unknown"
if (Test-Path ".\VERSION") {
    $currentVersion = (Get-Content ".\VERSION" -Raw).Trim()
    Info "Current version: $currentVersion"
}

# ── 2. Stash local changes ──────────────────────────────────
Info "Stashing local changes..."
$stashOutput = git stash 2>&1
$stashed = $false
if ($stashOutput -match "No local changes") {
    Warn "Nothing to stash - working directory is clean."
} else {
    Ok "Local changes stashed."
    $stashed = $true
}

# ── 3. Pull latest ──────────────────────────────────────────
Info "Pulling latest from origin/main..."
git pull origin main
if ($LASTEXITCODE -ne 0) {
    Err "git pull failed. Restoring your stash..."
    if ($stashed) { git stash pop }
    exit 1
}

$newVersion = "unknown"
if (Test-Path ".\VERSION") {
    $newVersion = (Get-Content ".\VERSION" -Raw).Trim()
}
Ok "Updated to version: $newVersion"

# ── 4. Pop stash ────────────────────────────────────────────
if ($stashed) {
    Info "Restoring local changes (git stash pop)..."
    $popOutput = git stash pop 2>&1
    Write-Host $popOutput

    $conflicts = git diff --name-only --diff-filter=U 2>&1
    if ($conflicts) {
        Warn "Merge conflicts detected in:"
        foreach ($f in $conflicts) { Warn "  $f" }
        Warn "Auto-resolving: keeping UPSTREAM for conflicted files..."

        foreach ($file in $conflicts) {
            # IMPORTANT: git gives paths relative to the repo root, but
            # [System.IO.File] methods resolve relative paths against
            # .NET's own internal current directory, not PowerShell's
            # $PWD - the two can silently diverge (e.g. after a
            # cross-drive cd), sending reads/writes to the wrong folder
            # entirely. Resolve to an absolute path first to avoid that.
            $fullPath = Join-Path $PWD.Path $file

            $raw = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
            $raw = $raw -replace '(?s)<<<<<<< Updated upstream\r?\n(.*?)=======.*?>>>>>>> Stashed changes\r?\n', '$1'
            $raw = $raw -replace '(?s)<<<<<<< Updated upstream\r?\n=======\r?\n[\r\n]*>>>>>>> Stashed changes\r?\n', ''
            [System.IO.File]::WriteAllText($fullPath, $raw, (New-Object System.Text.UTF8Encoding($false)))

            if (Has-ConflictMarkers $fullPath) {
                Err "Could not auto-resolve: $file - please fix manually."
                exit 1
            }

            git add $file
            Ok "Auto-resolved: $file"
        }

        # git stash pop does NOT drop the stash automatically when there
        # were conflicts, even after they're resolved and staged - without
        # this it lingers in `git stash list` and can cause confusion on
        # the next run.
        git stash drop
        Ok "Dropped resolved stash entry."
    } else {
        Ok "No conflicts - all local changes restored cleanly."
    }
}

# ── 5. Fix line endings on shell scripts ────────────────────
Info "Fixing line endings on .sh files..."
Get-ChildItem -Recurse -Filter "*.sh" | ForEach-Object {
    Fix-LineEndings $_.FullName
}

# ── 6. Build Docker image ───────────────────────────────────
if (-not (Test-Path ".\VERSION")) {
    Err "VERSION file not found."
    exit 1
}
$buildVersion = (Get-Content ".\VERSION" -Raw).Trim()
$tag = "${ImageName}:v${buildVersion}"

Info "VERSION file says: $buildVersion"
Info "Building Docker image: $tag ..."
docker build -t $tag .
if ($LASTEXITCODE -ne 0) {
    Err "Docker build failed."
    exit 1
}
Ok "Docker image built: $tag"

docker tag $tag "${ImageName}:latest"
Ok "Also tagged as: ${ImageName}:latest"

# ── 7. Summary ──────────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Update complete!" -ForegroundColor Green
Write-Host "  Version : $currentVersion  ->  $buildVersion" -ForegroundColor Green
Write-Host "  Image   : $tag" -ForegroundColor Green
Write-Host "  Image   : ${ImageName}:latest" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Warn "Next step: update your docker-compose.yaml image tag to: $tag"