$conflicts = @(
  'backend/app/schemas/data_source_registry.py',
  'backend/app/schemas/data_sources/configs.py',
  'frontend/layouts/default.vue',
  'frontend/layouts/users.vue',
  'locales/en.json'
)
foreach ($f in $conflicts) {
  $full = Join-Path $PWD.Path $f
  $raw = [System.IO.File]::ReadAllText($full, [System.Text.Encoding]::UTF8)
  $raw = $raw -replace '(?s)<<<<<<< Updated upstream\r?\n(.*?)=======.*?>>>>>>> Stashed changes\r?\n', '$1'
  $raw = $raw -replace '(?s)<<<<<<< Updated upstream\r?\n=======\r?\n[\r\n]*>>>>>>> Stashed changes\r?\n', ''
  [System.IO.File]::WriteAllText($full, $raw, (New-Object System.Text.UTF8Encoding($false)))
  git add $f
  Write-Host "Resolved: $f"
}