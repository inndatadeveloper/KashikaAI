# Step 1: Login to Keycloak
Write-Host "Step 1: Login to Keycloak..."
docker exec kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh config credentials `
  --server http://localhost:8080 `
  --realm master `
  --user admin `
  --password 36i5gKbBwfHf3zWZ

# Step 2: Disable SSL for master realm
Write-Host "Step 2: Disable SSL for master realm..."
docker exec kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh update realms/master `
  --server http://localhost:8080 --realm master --user admin --password 36i5gKbBwfHf3zWZ `
  -s sslRequired=NONE

# Step 3: Disable SSL for kashika-ai realm
Write-Host "Step 3: Disable SSL for kashika-ai realm..."
docker exec kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh update realms/kashika-ai `
  --server http://localhost:8080 --realm master --user admin --password 36i5gKbBwfHf3zWZ `
  -s sslRequired=NONE

# Step 4: Get kashika-ai client UUID
Write-Host "Step 4: Get kashika-ai client UUID..."
$CLIENT_UUID = docker exec kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh get clients `
  --server http://localhost:8080 `
  --realm master `
  --user admin `
  --password 36i5gKbBwfHf3zWZ `
  --target-realm kashika-ai `
  -q clientId=kashika-ai `
  --fields id 2>$null | Select-String '"id"' | ForEach-Object { $_ -replace '.*"id" : "(.*)".*', '$1' } | ForEach-Object { $_.Trim() }

Write-Host "Found client UUID: $CLIENT_UUID"

# Step 5: Update client secret
Write-Host "Step 5: Update client secret..."
docker exec kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh update clients/$CLIENT_UUID `
  --server http://localhost:8080 `
  --realm master `
  --user admin `
  --password 36i5gKbBwfHf3zWZ `
  --target-realm kashika-ai `
  -s secret=dnbm8NwQQXvpfciXHnepXzeMbL0VVduW

Write-Host "Done!"