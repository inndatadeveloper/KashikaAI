function Fix-Occurrence {
    param($path, $old, $new, $label)

    if (-not (Test-Path $path)) {
        Write-Host "[ERROR] Could not find $path" -ForegroundColor Red
        return
    }
    $fullPath = Join-Path $PWD.Path $path
    $raw = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
    $rawNormalized = $raw -replace "`r`n", "`n"

    if ($rawNormalized -notlike "*$old*") {
        Write-Host "[WARN] Could not find expected text in $path for '$label' - no change made." -ForegroundColor Yellow
        return
    }

    $fixed = $rawNormalized.Replace($old, $new)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($fullPath, $fixed, $utf8NoBom)
    Write-Host "[OK] Fixed '$label' in $path" -ForegroundColor Green
}

Fix-Occurrence -path "locales\en.json" `
    -old '"emptyTitle": "Make Bag of Words work with your tools",' `
    -new '"emptyTitle": "Make KashikaAI work with your tools",' `
    -label "Channels empty-state title"

Fix-Occurrence -path "frontend\components\McpModal.vue" `
    -old '"bagofwords": {' `
    -new '"kashikaai": {' `
    -label "MCP config key name"