Download the kashika-ai application Docker image from the Dockerhub
docker pull inndata/kashika-ai:v0.0.213
***********************************************************************************************************************************************************

Clone the project from the github and run the below command
docker compose up -d

connect to postgres container and run the below commands
docker exec -it kashika-ai-postgres psql -U kashika -d kashika
psql (16.11)
Type "help" for help.

kashika=# ALTER TABLE oauth_accounts ALTER COLUMN access_token TYPE TEXT;
ALTER TABLE
kashika=# ALTER TABLE oauth_accounts ALTER COLUMN refresh_token TYPE TEXT;
ALTER TABLE
kashika=# \q

***********************************************************************************************************************************************************
OpenLdap Login Credentials
Username: cn=admin,dc=kashika-ai,dc=local
Password: password123


Create Posix Group 
Click on --> dc=kashika-ai,dc=local
click on --> Create a child entry
Click on --> select Generic: Posix Group --> users (Add the value)
Click on --> create object --> commit

To Create Users
Click on --> dc=kashika-ai,dc=local
click on --> Create a child entry
Click on --> select Generic: User Account
			 First Name:
			 Last Name:
			 password: 
			 GID Number: select --> users
			 Login Shell: Bash
Click on --> create object --> commit
***********************************************************************************************************************************************************
Keycloak Setup

Open your browser and go to: http://localhost:8090
Click on "Administration Console"
Login with:

Username: admin
Password: admin
----------------------------------------------------------------------------------------------------------------------------
Step 1: Now we need to create the kashika-ai realm

Look at the top-left corner - you should see "Keycloak" or "Master" as the current realm
Click on the dropdown (where it says "Master")
Click "Create Realm" button

Fill in:
Realm name: kashika-ai
Click "Create"

You should now see "kashika-ai" in the realm dropdown.
----------------------------------------------------------------------------------------------------------------------------
Step 2: Create the OIDC client
Now we need to create the OAuth client that the bagofwords app will use:

In the left sidebar, click on "Clients"
Click "Create client" button
Fill in the form:

Client type: OpenID Connect
Client ID: kashika-ai

Click "Next"
On the "Capability config" page:

Client authentication: Turn ON (toggle to enabled)
Authorization: Leave OFF
Authentication flow: Check all the standard flows

Click "Next"
On the "Login settings" page, fill in:

Root URL: http://localhost:3000
Home URL: http://localhost:3000
Valid redirect URIs: http://localhost:3000/*
Valid post logout redirect URIs: http://localhost:3000/*
Web origins: http://localhost:3000

Click "Save"
***********************************************************************************************************************************************************
Step 3: Get the Client ID & Secret

Click on the "Credentials" tab (at the top, next to Settings, Keys, etc.)
You should see "Client secret" with a value. Copy that secret value and update in the below files.

File Name: bow-config.yaml change the below value client_secret with the copied value
    client_secret: CKUYEwWI4uVA6gceLhhwVoFk9MgTMs3H

File Name: docker-compose.yml change the below value BOW_CLIENT_SECRET with the copied value
    BOW_CLIENT_SECRET: "CKUYEwWI4uVA6gceLhhwVoFk9MgTMs3H"

The secret in your bow-config.yaml file looks like : WzhzqRQyIjvfApNGzT0V61sFIyHRXmT7

We need to check if the secret in Keycloak matches this one or update the copied value from the Client Secret. Restart the docker containers.
***********************************************************************************************************************************************************
Step 4: Click on User Fedaration and select Add LDAP provider
In Project root directory created a folder called Images. Open the image - KeyCloak-UserFederation and copy the values and click on save
***********************************************************************************************************************************************************
Optional Step if User doesnot have enough permissions like accessing dashboards, organizations, datasources etc.

Step 5: To add permissions for the users run the below commands in postgres container
docker exec -it kashika-ai-postgres psql -U kashika -d kashika

-- Create an organization
INSERT INTO organizations (id, name, description, created_at, updated_at) 
VALUES (
  '00000000-0000-0000-0000-000000000001', 
  'My Organization', 
  'Default organization', 
  NOW(), 
  NOW()
);

-- Copy last_login value from users table and insert into membership table
select * from users;

-- Create membership (linking your user to the organization as admin)
INSERT INTO memberships (
  id, 
  user_id, 
  organization_id, 
  role, 
  email, 
  created_at, 
  updated_at
) VALUES (
  '00000000-0000-0000-0000-000000000002',
  'a56ae6c4-fa1a-4b6d-b628-32a4db47abd6',  -- Your user ID
  '00000000-0000-0000-0000-000000000001',  -- Organization ID we just created
  'admin',
  'developer@inndata.in',
  NOW(),
  NOW()
);

-- Verify it was created
SELECT * FROM memberships;

user_id                |           organization_id            | role  |                  id                  |        email         | invite_token |         created_at         |         updated_at         | deleted_at 
--------------------------------------+--------------------------------------+-------+--------------------------------------+----------------------+--------------+----------------------------+----------------------------+------------
 0a279803-8532-4b43-afe3-3169dbb8aad5 | 00000000-0000-0000-0000-000000000001 | admin | 00000000-0000-0000-0000-000000000002 | developer@inndata.in |              | 2025-10-26 01:46:57.604573 | 2025-10-26 01:46:57.604573 | 
(1 row)

-- Verify user is now linked to organization
SELECT u.email, m.role, o.name as organization
FROM users u
JOIN memberships m ON u.id = m.user_id
JOIN organizations o ON m.organization_id = o.id;

        email         | role  |  organization   
----------------------+-------+-----------------
 developer@inndata.in | admin | My Organization


-- TO add new user and give permissions for new user
-- Use the ACTUAL user ID from your SELECT query
INSERT INTO memberships (
  id, 
  user_id, 
  organization_id, 
  role, 
  email, 
  created_at, 
  updated_at
) VALUES (
  gen_random_uuid(),
  '883aeda5-91d9-4812-8ab1-9fef1750ea11',  -- ACTUAL user ID
  '00000000-0000-0000-0000-000000000001',  -- Your organization ID
  'member',  -- or 'admin' for admin access
  'rahulgupta@inndata.in',
  NOW(),
  NOW()
);

-- Verify
SELECT u.email, m.role, o.name as organization
FROM users u
JOIN memberships m ON u.id = m.user_id
JOIN organizations o ON m.organization_id = o.id;

Step 6: To configure your LLM goto Settings.
Settings --> LLM --> Integrate Models --> New Provider --> OpenAI --> Name --> Api Key --> 