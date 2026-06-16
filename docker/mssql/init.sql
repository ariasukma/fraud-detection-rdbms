IF DB_ID('fraud_db') IS NULL
BEGIN
  CREATE DATABASE fraud_db;
END
GO

USE fraud_db;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'fraud_user')
BEGIN
  CREATE LOGIN fraud_user WITH PASSWORD = 'fraud_password', CHECK_POLICY = OFF;
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'fraud_user')
BEGIN
  CREATE USER fraud_user FOR LOGIN fraud_user;
END
GO

ALTER ROLE db_owner ADD MEMBER fraud_user;
GO

