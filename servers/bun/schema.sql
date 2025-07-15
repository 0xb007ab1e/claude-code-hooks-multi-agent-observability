CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_app TEXT NOT NULL,
  session_id TEXT NOT NULL,
  hook_event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  chat TEXT,
  summary TEXT,
  timestamp INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_app ON events(source_app);
CREATE INDEX IF NOT EXISTS idx_session_id ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_hook_event_type ON events(hook_event_type);
CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);

CREATE TABLE IF NOT EXISTS themes (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  displayName TEXT NOT NULL,
  description TEXT,
  colors TEXT NOT NULL,
  isPublic INTEGER NOT NULL DEFAULT 0,
  authorId TEXT,
  authorName TEXT,
  createdAt INTEGER NOT NULL,
  updatedAt INTEGER NOT NULL,
  tags TEXT,
  downloadCount INTEGER DEFAULT 0,
  rating REAL DEFAULT 0,
  ratingCount INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_themes_name ON themes(name);
CREATE INDEX IF NOT EXISTS idx_themes_isPublic ON themes(isPublic);
CREATE INDEX IF NOT EXISTS idx_themes_createdAt ON themes(createdAt);

