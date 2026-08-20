-- Optional manual bootstrap for JOFA MySQL database.
-- Prefer: python scripts/init_mysql.py

CREATE DATABASE IF NOT EXISTS jofa
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Optional dedicated user (adjust password):
-- CREATE USER IF NOT EXISTS 'jofa'@'%' IDENTIFIED BY 'change_me';
-- GRANT ALL PRIVILEGES ON jofa.* TO 'jofa'@'%';
-- FLUSH PRIVILEGES;
