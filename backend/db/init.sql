CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    file_path VARCHAR(512) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL
);