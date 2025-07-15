-- Initialize database schema for multi-agent observability tests
-- Database already exists, just connect to it
\c testdb;

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    source_app VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    hook_event_type VARCHAR(255) NOT NULL,
    payload JSONB,
    chat TEXT,
    summary TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source_app ON events(source_app);
CREATE INDEX IF NOT EXISTS idx_events_hook_event_type ON events(hook_event_type);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE testdb TO "user";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "user";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "user";
