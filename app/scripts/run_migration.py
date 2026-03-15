"""
Script to add missing columns to users table.
Run this in SQL Server Management Studio (SSMS).
"""

print("Run this SQL in SSMS to add missing columns:\n")

print("""
-- Add must_change_password column to users table if not exists
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'must_change_password')
BEGIN
    ALTER TABLE users ADD must_change_password BIT NOT NULL DEFAULT 1
    PRINT 'Column must_change_password added to users table!'
END
ELSE
BEGIN
    PRINT 'Column must_change_password already exists!'
END

-- Create password_reset_tokens table if not exists
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'password_reset_tokens')
BEGIN
    CREATE TABLE password_reset_tokens (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL,
        token NVARCHAR(64) NOT NULL UNIQUE,
        expires_at DATETIME NOT NULL,
        used_at DATETIME NULL,
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    
    CREATE INDEX IX_password_reset_tokens_user_id ON password_reset_tokens(user_id)
    CREATE INDEX IX_password_reset_tokens_token ON password_reset_tokens(token)
    CREATE INDEX IX_password_reset_tokens_expires_at ON password_reset_tokens(expires_at)
    
    PRINT 'Table password_reset_tokens created successfully!'
END
ELSE
BEGIN
    PRINT 'Table password_reset_tokens already exists!'
END
""")
