import sqlite3
import json
import time
from typing import List
from models import HookEvent, FilterOptions, Theme, ThemeSearchQuery, ApiResponse
from config import settings


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._connection = None
        # For in-memory databases, we need to maintain a persistent connection
        if self.db_path == ':memory:':
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.init_database()

    def _get_connection(self):
        """Get a database connection"""
        if self._connection:
            return self._connection
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize the database with required tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create events table
        cursor.execute('''
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
        ''')

        # Create themes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS themes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                displayName TEXT NOT NULL,
                description TEXT,
                colors TEXT NOT NULL,
                isPublic BOOLEAN NOT NULL,
                authorId TEXT,
                authorName TEXT,
                createdAt INTEGER NOT NULL,
                updatedAt INTEGER NOT NULL,
                tags TEXT NOT NULL,
                downloadCount INTEGER DEFAULT 0,
                rating REAL,
                ratingCount INTEGER DEFAULT 0
            )
        ''')

        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_source_app ON events(source_app)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_hook_event_type ON events(hook_event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_themes_name ON themes(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_themes_author ON themes(authorId)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_themes_public ON themes(isPublic)')

        conn.commit()

    def insert_event(self, event: HookEvent) -> HookEvent:
        """Insert a new event into the database"""
        conn = self._get_connection()
        cursor = conn.cursor()

        timestamp = event.timestamp or int(time.time() * 1000)

        cursor.execute('''
            INSERT INTO events (source_app, session_id, hook_event_type, payload, chat, summary, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.source_app,
            event.session_id,
            event.hook_event_type,
            json.dumps(event.payload),
            json.dumps(event.chat) if event.chat else None,
            event.summary,
            timestamp
        ))

        event_id = cursor.lastrowid
        conn.commit()

        # Return the event with the generated ID
        event.id = event_id
        event.timestamp = timestamp
        return event

    def get_recent_events(self, limit: int = 100, offset: int = 0) -> List[HookEvent]:
        """Get recent events from the database with pagination support"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, source_app, session_id, hook_event_type, payload, chat, summary, timestamp
            FROM events
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        events = []
        for row in cursor.fetchall():
            event = HookEvent(
                id=row[0],
                source_app=row[1],
                session_id=row[2],
                hook_event_type=row[3],
                payload=json.loads(row[4]),
                chat=json.loads(row[5]) if row[5] else None,
                summary=row[6],
                timestamp=row[7]
            )
            events.append(event)

        return events

    def get_filter_options(self) -> FilterOptions:
        """Get available filter options"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get unique source apps
        cursor.execute('SELECT DISTINCT source_app FROM events ORDER BY source_app')
        source_apps = [row[0] for row in cursor.fetchall()]

        # Get unique session IDs
        cursor.execute('SELECT DISTINCT session_id FROM events ORDER BY session_id')
        session_ids = [row[0] for row in cursor.fetchall()]

        # Get unique hook event types
        cursor.execute('SELECT DISTINCT hook_event_type FROM events ORDER BY hook_event_type')
        hook_event_types = [row[0] for row in cursor.fetchall()]

        return FilterOptions(
            source_apps=source_apps,
            session_ids=session_ids,
            hook_event_types=hook_event_types
        )

    def get_event_count(self) -> int:
        """Get the total number of events"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM events')
        return cursor.fetchone()[0]

    def create_theme(self, theme: Theme) -> ApiResponse:
        """Create a new theme"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if theme already exists
                cursor.execute('SELECT id FROM themes WHERE id = ?', (theme.id,))
                if cursor.fetchone():
                    return ApiResponse(
                        success=False,
                        error=f'Theme with ID {theme.id} already exists'
                    )

                cursor.execute('''
                    INSERT INTO themes (id, name, displayName, description, colors, isPublic,
                                      authorId, authorName, createdAt, updatedAt, tags,
                                      downloadCount, rating, ratingCount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    theme.id,
                    theme.name,
                    theme.displayName,
                    theme.description,
                    json.dumps(theme.colors.dict()),
                    theme.isPublic,
                    theme.authorId,
                    theme.authorName,
                    theme.createdAt,
                    theme.updatedAt,
                    json.dumps(theme.tags),
                    theme.downloadCount,
                    theme.rating,
                    theme.ratingCount
                ))

                conn.commit()

                return ApiResponse(
                    success=True,
                    data=theme,
                    message='Theme created successfully'
                )
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e)
            )

    def get_theme_by_id(self, theme_id: str) -> ApiResponse:
        """Get a theme by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM themes WHERE id = ?', (theme_id,))
                row = cursor.fetchone()

                if not row:
                    return ApiResponse(
                        success=False,
                        error='Theme not found'
                    )

                theme = Theme(
                    id=row[0],
                    name=row[1],
                    displayName=row[2],
                    description=row[3],
                    colors=json.loads(row[4]),
                    isPublic=bool(row[5]),
                    authorId=row[6],
                    authorName=row[7],
                    createdAt=row[8],
                    updatedAt=row[9],
                    tags=json.loads(row[10]),
                    downloadCount=row[11],
                    rating=row[12],
                    ratingCount=row[13]
                )

                return ApiResponse(
                    success=True,
                    data=theme
                )
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e)
            )

    def search_themes(self, query: ThemeSearchQuery) -> ApiResponse:
        """Search themes based on query parameters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Build WHERE clause
                where_conditions = []
                params = []

                if query.query:
                    where_conditions.append('(name LIKE ? OR displayName LIKE ? OR description LIKE ?)')
                    search_term = f'%{query.query}%'
                    params.extend([search_term, search_term, search_term])

                if query.authorId:
                    where_conditions.append('authorId = ?')
                    params.append(query.authorId)

                if query.isPublic is not None:
                    where_conditions.append('isPublic = ?')
                    params.append(query.isPublic)

                where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'

                # Build ORDER BY clause
                order_by = 'name ASC'
                if query.sortBy:
                    order_direction = 'DESC' if query.sortOrder == 'desc' else 'ASC'
                    if query.sortBy == 'created':
                        order_by = f'createdAt {order_direction}'
                    elif query.sortBy == 'updated':
                        order_by = f'updatedAt {order_direction}'
                    elif query.sortBy == 'downloads':
                        order_by = f'downloadCount {order_direction}'
                    elif query.sortBy == 'rating':
                        order_by = f'rating {order_direction}'
                    else:
                        order_by = f'name {order_direction}'

                # Execute query
                sql = f'''
                    SELECT * FROM themes
                    WHERE {where_clause}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                '''
                params.extend([query.limit, query.offset])

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                themes = []
                for row in rows:
                    theme = Theme(
                        id=row[0],
                        name=row[1],
                        displayName=row[2],
                        description=row[3],
                        colors=json.loads(row[4]),
                        isPublic=bool(row[5]),
                        authorId=row[6],
                        authorName=row[7],
                        createdAt=row[8],
                        updatedAt=row[9],
                        tags=json.loads(row[10]),
                        downloadCount=row[11],
                        rating=row[12],
                        ratingCount=row[13]
                    )
                    themes.append(theme)

                return ApiResponse(
                    success=True,
                    data=themes
                )
        except Exception as e:
            return ApiResponse(
                success=False,
                error=str(e)
            )


# Global database instance
db = Database()
