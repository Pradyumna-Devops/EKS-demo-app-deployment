CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE
);

INSERT INTO users (name, email)
VALUES
    ('Pradyumna', 'pradyumna@example.com'),
    ('John Doe', 'john@example.com'),
    ('Jane Smith', 'jane@example.com')
ON CONFLICT (email) DO NOTHING;
