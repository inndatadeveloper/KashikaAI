$path = "frontend\components\UserProfileModal.vue"

if (-not (Test-Path $path)) {
    Write-Host "[ERROR] Could not find $path - run this from D:\KashikaAI" -ForegroundColor Red
    exit 1
}

$fullPath = Join-Path $PWD.Path $path
$raw = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
$rawNormalized = $raw -replace "`r`n", "`n"

$old = 'mcpServers: { bagofwords: {'
$new = 'mcpServers: { kashikaai: {'

if ($rawNormalized -notlike "*$old*") {
    Write-Host "[WARN] Could not find expected text in $path - no change made." -ForegroundColor Yellow
    exit 1
}

$fixed = $rawNormalized.Replace($old, $new)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($fullPath, $fixed, $utf8NoBom)
Write-Host "[OK] Fixed MCP config key in $path" -ForegroundColor Green