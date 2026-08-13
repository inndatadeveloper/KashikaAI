$path = "frontend\layouts\settings.vue"

if (-not (Test-Path $path)) {
    Write-Host "[ERROR] Could not find $path - run this from D:\KashikaAI" -ForegroundColor Red
    exit 1
}

$fullPath = Join-Path $PWD.Path $path
$raw = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
$rawNormalized = $raw -replace "`r`n", "`n"

$linesToRemove = @(
    "    { name: 'audit', label: 'settings.auditLogs', requiredPermission: `"view_audit_logs`" },`n",
    "    { name: 'identity-provider', label: 'settings.identityProviderTab', requiredPermission: `"manage_identity_providers`" },`n",
    "    { name: 'license', label: 'settings.license', requiredPermission: `"manage_settings`" },`n"
)

$fixed = $rawNormalized
$allFound = $true
foreach ($line in $linesToRemove) {
    if ($fixed -notlike "*$line*") {
        Write-Host "[WARN] Could not find exact line: $line" -ForegroundColor Yellow
        $allFound = $false
        continue
    }
    $fixed = $fixed.Replace($line, "")
}

if (-not $allFound) {
    Write-Host "[ERROR] Not all expected lines were found - no change made. Check the file manually." -ForegroundColor Red
    exit 1
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($fullPath, $fixed, $utf8NoBom)
Write-Host "[OK] Removed Audit Logs, Identity Provider, and License tabs from $path" -ForegroundColor Green