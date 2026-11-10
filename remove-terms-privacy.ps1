$path = "frontend\pages\users\sign-up.vue"

if (-not (Test-Path $path)) {
    Write-Host "[ERROR] Could not find $path" -ForegroundColor Red
    exit 1
}

$fullPath = Join-Path $PWD.Path $path
$raw = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
$rawNormalized = $raw -replace "`r`n", "`n"

$pattern = '(?s)\n\s*<p class="mt-6 text-xs leading-relaxed text-center text-gray-400 dark:text-gray-500">\s*\n\s*\{\{ \$t\(''auth\.termsPrefix''\) \}\}.*?</p>\n'

if ($rawNormalized -notmatch $pattern) {
    Write-Host "[INFO] Terms/Privacy block not found - already removed or file changed." -ForegroundColor Cyan
    exit 0
}

$fixed = $rawNormalized -replace $pattern, "`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($fullPath, $fixed, $utf8NoBom)
Write-Host "[OK] Removed Terms of Service / Privacy Policy line from $path" -ForegroundColor Green