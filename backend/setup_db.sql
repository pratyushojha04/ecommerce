CREATE DATABASE IF NOT EXISTS sello_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'sello_user'@'localhost' IDENTIFIED BY 'sello_password';
GRANT ALL PRIVILEGES ON sello_db.* TO 'sello_user'@'localhost';
FLUSH PRIVILEGES;
