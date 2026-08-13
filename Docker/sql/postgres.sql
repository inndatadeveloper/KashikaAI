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
