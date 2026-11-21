CREATE TABLE Users (
    UserId INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL UNIQUE,
    DisplayName TEXT NOT NULL,
    PasswordHash TEXT NOT NULL,
    PasswordSalt TEXT NOT NULL,
    Role TEXT NOT NULL DEFAULT 'USER'
        CHECK (Role IN ('USER', 'ADMIN')),
    IsBlocked INTEGER NOT NULL DEFAULT 0
        CHECK (IsBlocked IN (0, 1)),
    IsDeleted INTEGER NOT NULL DEFAULT 0
        CHECK (IsDeleted IN (0, 1)),
    CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE Chats (
    ChatId INTEGER PRIMARY KEY AUTOINCREMENT,
    CreatedAt TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE ChatMembers (
    ChatId INTEGER NOT NULL,
    UserId INTEGER NOT NULL,
    ClearedAt TEXT,
    PRIMARY KEY (ChatId, UserId),

    FOREIGN KEY (ChatId)
        REFERENCES Chats(ChatId)
        ON DELETE CASCADE,

    FOREIGN KEY (UserId)
        REFERENCES Users(UserId)
        ON DELETE CASCADE
);

CREATE TABLE Messages (
    MessageId INTEGER PRIMARY KEY AUTOINCREMENT,
    ChatId INTEGER NOT NULL,
    SenderId INTEGER NOT NULL,
    Text TEXT NOT NULL,
    SentAt TEXT NOT NULL DEFAULT (datetime('now')),
    ReadAt TEXT,
    IsDeleted INTEGER NOT NULL DEFAULT 0
        CHECK (IsDeleted IN (0, 1)),

    FOREIGN KEY (ChatId)
        REFERENCES Chats(ChatId)
        ON DELETE CASCADE,

    FOREIGN KEY (SenderId)
        REFERENCES Users(UserId)
        ON DELETE CASCADE
);

CREATE TABLE Sessions (
    SessionId INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER NOT NULL,
    Token TEXT NOT NULL UNIQUE,
    CreatedAt TEXT NOT NULL DEFAULT (datetime('now')),
    ExpiresAt TEXT,
    IsActive INTEGER NOT NULL DEFAULT 1
        CHECK (IsActive IN (0, 1)),

    FOREIGN KEY (UserId)
        REFERENCES Users(UserId)
        ON DELETE CASCADE
);

CREATE TABLE AuditLog (
    LogId INTEGER PRIMARY KEY AUTOINCREMENT,
    UserId INTEGER,
    EventType TEXT NOT NULL,
    Description TEXT,
    CreatedAt TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (UserId)
        REFERENCES Users(UserId)
        ON DELETE SET NULL
);