CREATE TABLE user (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    display TEXT NOT NULL,
    registered INT NOT NULL,
    billable INT NOT NULL,
    ready BOOLEAN NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    scopes TEXT NOT NULL,
    time_authorized TEXT NOT NULL,
    time_authorized_original TEXT NOT NULL
);
