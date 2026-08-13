$path = "frontend\layouts\default.vue"

$old = @'
    // Documentation + MCP Server + GitHub moved out of the main sidebar into this menu.
    const resources: any[] = [{
      label: t('changelog.menuItem'),
      icon: 'heroicons-document-text',
      click: () => { showChangelogModal.value = true }
    }, {
      label: t('nav.documentation'),
      icon: 'heroicons-book-open',
      click: () => { window.open('https://docs.bagofwords.com', '_blank', 'noopener') }
    }]
    if (isMcpEnabled.value && useCan('manage_settings')) {
      resources.push({
        label: t('nav.mcpServer'),
        iconComponent: markRaw(McpIcon),
        click: () => { showMcpModal.value = true }
      })
    }
    resources.push({
      label: t('nav.starOnGithub'),
      iconComponent: markRaw(GithubIcon),
      click: () => { window.open('https://github.com/bagofwords1/bagofwords', '_blank', 'noopener') }
    })
    groups.push(resources)
'@

$new = @'
    // Documentation + Changelog + GitHub hidden from this menu. MCP Server kept.
    const resources: any[] = []
    if (isMcpEnabled.value && useCan('manage_settings')) {
      resources.push({
        label: t('nav.mcpServer'),
        iconComponent: markRaw(McpIcon),
        click: () => { showMcpModal.value = true }
      })
    }
    if (resources.length) groups.push(resources)
'@

if (-not (Test-Path $path)) {
    Write-Host "[ERROR] Could not find $path - run this from D:\KashikaAI" -ForegroundColor Red
    exit 1
}

$fullPath = Join-Path $PWD.Path $path
$raw = [System.IO.File]::ReadAllText($fullPath, [System.Text.Encoding]::UTF8)
$rawNormalized = $raw -replace "`r`n", "`n"
$oldNormalized = $old -replace "`r`n", "`n"

if ($rawNormalized -notmatch [regex]::Escape($oldNormalized)) {
    Write-Host "[WARN] Expected block not found (file may already differ from what we expect) - no change made. Check manually." -ForegroundColor Yellow
    exit 1
}

$fixed = $rawNormalized -replace [regex]::Escape($oldNormalized), ($new -replace "`r`n", "`n")
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($fullPath, $fixed, $utf8NoBom)
Write-Host "[OK] Removed Changelog, Documentation, and Star on GitHub from the user menu in $path" -ForegroundColor Green