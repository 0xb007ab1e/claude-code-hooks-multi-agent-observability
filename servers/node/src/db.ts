import Database, { Database as DatabaseType } from 'better-sqlite3';
import type { HookEvent, FilterOptions, Theme, ThemeSearchQuery } from './types.js';
import { config } from './config.js';

let db: DatabaseType;

export function initDatabase(): void {
  db = new Database(config.DATABASE_PATH);
  
  // Enable WAL mode for better concurrent performance
  db.exec('PRAGMA journal_mode = WAL');
  db.exec('PRAGMA synchronous = NORMAL');
  
  // Create events table
  db.exec(`
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_app TEXT NOT NULL,
      session_id TEXT NOT NULL,
      hook_event_type TEXT NOT NULL,
      payload TEXT NOT NULL,
      chat TEXT,
      summary TEXT,
      timestamp INTEGER NOT NULL
    )
  `);
  
  // Create themes table
  db.exec(`
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
    )
  `);
}

export function insertEvent(event: HookEvent): HookEvent {
  const stmt = db.prepare(`
    INSERT INTO events (source_app, session_id, hook_event_type, payload, chat, summary, timestamp)
    VALUES (@source_app, @session_id, @hook_event_type, @payload, @chat, @summary, @timestamp)
  `);

  const timestamp = event.timestamp || Date.now();
  const result = stmt.run({
    source_app: event.source_app,
    session_id: event.session_id,
    hook_event_type: event.hook_event_type,
    payload: JSON.stringify(event.payload),
    chat: event.chat ? JSON.stringify(event.chat) : null,
    summary: event.summary || null,
    timestamp
  });

  return {
    ...event,
    id: result.lastInsertRowid as number,
    timestamp
  };
}

export function getFilterOptions(): FilterOptions {
  const sourceApps = db.prepare('SELECT DISTINCT source_app FROM events ORDER BY source_app').all() as { source_app: string }[];
  const sessionIds = db.prepare('SELECT DISTINCT session_id FROM events ORDER BY session_id DESC LIMIT 100').all() as { session_id: string }[];
  const hookEventTypes = db.prepare('SELECT DISTINCT hook_event_type FROM events ORDER BY hook_event_type').all() as { hook_event_type: string }[];
  
  return {
    source_apps: sourceApps.map(row => row.source_app),
    session_ids: sessionIds.map(row => row.session_id),
    hook_event_types: hookEventTypes.map(row => row.hook_event_type)
  };
}

export function getRecentEvents(limit: number = 100): HookEvent[] {
  const stmt = db.prepare(`
    SELECT id, source_app, session_id, hook_event_type, payload, chat, summary, timestamp
    FROM events
    ORDER BY timestamp DESC
    LIMIT ?
  `);
  
  const rows = stmt.all(limit) as any[];
  
  return rows.map(row => ({
    ...row,
    payload: JSON.parse(row.payload),
    chat: row.chat ? JSON.parse(row.chat) : undefined
  })).reverse();
}

// Theme database functions
export function insertTheme(theme: Theme): Theme {
  const stmt = db.prepare(`
    INSERT INTO themes (id, name, displayName, description, colors, isPublic, authorId, authorName, createdAt, updatedAt, tags, downloadCount, rating, ratingCount)
    VALUES (@id, @name, @displayName, @description, @colors, @isPublic, @authorId, @authorName, @createdAt, @updatedAt, @tags, @downloadCount, @rating, @ratingCount)
  `);
  
  stmt.run({
    id: theme.id,
    name: theme.name,
    displayName: theme.displayName,
    description: theme.description || null,
    colors: JSON.stringify(theme.colors),
    isPublic: theme.isPublic ? 1 : 0,
    authorId: theme.authorId || null,
    authorName: theme.authorName || null,
    createdAt: theme.createdAt,
    updatedAt: theme.updatedAt,
    tags: JSON.stringify(theme.tags),
    downloadCount: theme.downloadCount || 0,
    rating: theme.rating || 0,
    ratingCount: theme.ratingCount || 0
  });
  
  return theme;
}

export function updateTheme(id: string, updates: Partial<Theme>): boolean {
  const allowedFields = ['displayName', 'description', 'colors', 'isPublic', 'updatedAt', 'tags'];
  const validKeys = Object.keys(updates)
    .filter(key => allowedFields.includes(key) && updates[key as keyof Theme] !== undefined);
  
  if (validKeys.length === 0) return false;
  
  const setClause = validKeys.map(key => `${key} = @${key}`).join(', ');
  
  const params: any = { id };
  for (const key of validKeys) {
    const value = updates[key as keyof Theme];
    if (key === 'colors' || key === 'tags') {
      params[key] = JSON.stringify(value);
    } else if (key === 'isPublic') {
      params[key] = value ? 1 : 0;
    } else {
      params[key] = value;
    }
  }
  
  const stmt = db.prepare(`UPDATE themes SET ${setClause} WHERE id = @id`);
  const result = stmt.run(params);
  
  return result.changes > 0;
}

export function getTheme(id: string): Theme | null {
  const stmt = db.prepare('SELECT * FROM themes WHERE id = ?');
  const row = stmt.get(id) as any;
  
  if (!row) return null;
  
  return {
    id: row.id,
    name: row.name,
    displayName: row.displayName,
    description: row.description,
    colors: JSON.parse(row.colors),
    isPublic: Boolean(row.isPublic),
    authorId: row.authorId,
    authorName: row.authorName,
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
    tags: JSON.parse(row.tags || '[]'),
    downloadCount: row.downloadCount,
    rating: row.rating,
    ratingCount: row.ratingCount
  };
}

export function getThemes(query: ThemeSearchQuery = {}): Theme[] {
  let sql = 'SELECT * FROM themes WHERE 1=1';
  const params: any = {};
  
  if (query.isPublic !== undefined) {
    sql += ' AND isPublic = @isPublic';
    params.isPublic = query.isPublic ? 1 : 0;
  }
  
  if (query.authorId) {
    sql += ' AND authorId = @authorId';
    params.authorId = query.authorId;
  }
  
  if (query.query) {
    sql += ' AND (name LIKE @searchTerm OR displayName LIKE @searchTerm OR description LIKE @searchTerm)';
    params.searchTerm = `%${query.query}%`;
  }
  
  // Add sorting
  const sortBy = query.sortBy || 'created';
  const sortOrder = query.sortOrder || 'desc';
  const sortColumn = {
    name: 'name',
    created: 'createdAt',
    updated: 'updatedAt',
    downloads: 'downloadCount',
    rating: 'rating'
  }[sortBy] || 'createdAt';
  
  sql += ` ORDER BY ${sortColumn} ${sortOrder.toUpperCase()}`;
  
  // Add pagination
  if (query.limit) {
    sql += ' LIMIT @limit';
    params.limit = query.limit;
    
    if (query.offset) {
      sql += ' OFFSET @offset';
      params.offset = query.offset;
    }
  }
  
  const stmt = db.prepare(sql);
  const rows = stmt.all(params) as any[];
  
  return rows.map(row => ({
    id: row.id,
    name: row.name,
    displayName: row.displayName,
    description: row.description,
    colors: JSON.parse(row.colors),
    isPublic: Boolean(row.isPublic),
    authorId: row.authorId,
    authorName: row.authorName,
    createdAt: row.createdAt,
    updatedAt: row.updatedAt,
    tags: JSON.parse(row.tags || '[]'),
    downloadCount: row.downloadCount,
    rating: row.rating,
    ratingCount: row.ratingCount
  }));
}

export function deleteTheme(id: string): boolean {
  const stmt = db.prepare('DELETE FROM themes WHERE id = ?');
  const result = stmt.run(id);
  return result.changes > 0;
}

export function incrementThemeDownloadCount(id: string): boolean {
  const stmt = db.prepare('UPDATE themes SET downloadCount = downloadCount + 1 WHERE id = ?');
  const result = stmt.run(id);
  return result.changes > 0;
}

export function getEventCount(): number {
  const stmt = db.prepare('SELECT COUNT(*) as count FROM events');
  const result = stmt.get() as { count: number };
  return result.count;
}
