#!/bin/bash

echo "Step 1: Login to Keycloak..."
docker exec -it kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password 36i5gKbBwfHf3zWZ

echo "Step 2: Disable SSL for master realm..."
docker exec -it kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh update realms/master \
  --server http://localhost:8080 --realm master --user admin --password 36i5gKbBwfHf3zWZ \
  -s sslRequired=NONE

echo "Step 3: Disable SSL for kashika-ai realm..."
docker exec -it kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh update realms/kashika-ai \
  --server http://localhost:8080 --realm master --user admin --password 36i5gKbBwfHf3zWZ \
  -s sslRequired=NONE

echo "Step 4: Get kashika-ai client UUID..."
CLIENT_UUID=$(docker exec kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh get clients \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password 36i5gKbBwfHf3zWZ \
  --target-realm kashika-ai \
  -q clientId=kashika-ai \
  --fields id 2>/dev/null | grep '"id"' | sed 's/.*"\(.*\)".*/\1/')

echo "Found client UUID: $CLIENT_UUID"

echo "Step 5: Update client secret..."
docker exec -it kashika-ai-keycloak /opt/keycloak/bin/kcadm.sh update clients/$CLIENT_UUID \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password 36i5gKbBwfHf3zWZ \
  --target-realm kashika-ai \
  -s secret=dnbm8NwQQXvpfciXHnepXzeMbL0VVduW

echo "Done!"
