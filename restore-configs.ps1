$path = "backend\app\schemas\data_sources\configs.py"

$missingBlock = @'
# Tally
class TallyConfig(BaseModel):
    host: str = Field("localhost", title="Host", description="Tally server hostname or IP", json_schema_extra={"ui:type": "string"})
    port: int = Field(9000, title="Port", description="Tally gateway port (default: 9000)", json_schema_extra={"ui:type": "number"})
class TallyCredentials(BaseModel):
    pass  # Tally uses host/port only, no credentials needed by default
# SAP S/4HANA
class SapS4hanaConfig(BaseModel):
    host: str = Field(..., title="Host", description="SAP S/4HANA hostname or IP", json_schema_extra={"ui:type": "string"})
    port: int = Field(443, title="Port", description="Port (default: 443 for HTTPS)", json_schema_extra={"ui:type": "number"})
    client_id: str = Field(..., title="SAP Client", description="SAP client number (e.g. 100)", json_schema_extra={"ui:type": "string"})
    use_ssl: bool = Field(True, title="Use SSL", description="Use HTTPS connection", json_schema_extra={"ui:type": "toggle"})
class SapS4hanaCredentials(BaseModel):
    username: str = Field(..., title="Username", description="SAP username", json_schema_extra={"ui:type": "string"})
    password: str = Field(..., title="Password", description="SAP password", json_schema_extra={"ui:type": "password"})
# Zoho Books
class ZohoBooksConfig(BaseModel):
    organization_id: str = Field(..., title="Organization ID", description="Zoho Books Organization ID", json_schema_extra={"ui:type": "string"})
    region: str = Field("com", title="Region", description="Zoho region: com, eu, in, com.au, jp", json_schema_extra={"ui:type": "string"})
class ZohoBooksCredentials(BaseModel):
    access_token: str = Field(..., title="Access Token", description="Zoho OAuth2 access token", json_schema_extra={"ui:type": "password"})
'@

if (-not (Test-Path $path)) {
    Write-Host "[ERROR] Could not find $path - run this from D:\KashikaAI" -ForegroundColor Red
    exit 1
}

$lines = Get-Content $path -Encoding UTF8
$allIndex = ($lines | Select-String -Pattern '^__all__ = \[').LineNumber
if (-not $allIndex) {
    Write-Host "[ERROR] Could not find '__all__ = [' in $path - aborting, nothing changed." -ForegroundColor Red
    exit 1
}
$insertAt = $allIndex - 1   # 0-based index of the __all__ line

if ((Get-Content $path -Raw) -match 'class TallyConfig') {
    Write-Host "[INFO] TallyConfig already present - nothing to do." -ForegroundColor Cyan
    exit 0
}

$before = $lines[0..($insertAt - 1)]
$after  = $lines[$insertAt..($lines.Count - 1)]
$newLines = $before + ($missingBlock -split "`r?`n") + $after

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path $path), ($newLines -join "`n") + "`n", $utf8NoBom)

Write-Host "[OK] Restored TallyConfig, SapS4hanaConfig, ZohoBooksConfig (+ their Credentials classes) into $path" -ForegroundColor Green