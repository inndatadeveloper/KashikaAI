$files = @(
  "frontend\layouts\default.vue",
  "frontend\layouts\users.vue"
)

foreach ($f in $files) {
    if (-not (Test-Path $f)) {
        Write-Host "[ERROR] Could not find $f - run this from D:\KashikaAI" -ForegroundColor Red
        continue
    }
    $fullPath = Join-Path $PWD.Path $f
    $raw = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
    if ($raw -notmatch "environment === 'production' && intercom\)") {
        Write-Host "[WARN] Expected guard text not found in $f - no change made. Check manually." -ForegroundColor Yellow
        continue
    }
    $fixed = $raw -replace "environment === 'production' && intercom\)", "environment === 'production' && intercom?.enabled)"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($fullPath, $fixed, $utf8NoBom)
    Write-Host "[OK] Fixed intercom guard in $f" -ForegroundColor Green
}