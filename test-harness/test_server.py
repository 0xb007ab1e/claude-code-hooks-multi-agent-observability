#!/usr/bin/env python3
"""
Multi-database FastAPI server that supports PostgreSQL, MongoDB, and SQLite
for comprehensive E2E testing of the observability framework.
"""

import os
import json
import time
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from config.port_manager import get_port, assign_port

# Optional database imports
try:
    import psycopg2
    import psycopg2.extras
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

try:
    from pymongo import MongoClient
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

# Pydantic models
class HookEvent(BaseModel):
    source_app: str
    session_id: str
    hook_event_type: str
    payload: Dict[str, Any]
    chat: Optional[str] = None
    summary: Optional[str] = None
    timestamp: Optional[int] = None

class EventResponse(BaseModel):
    id: int
    source_app: str
    session_id: str
    hook_event_type: str
    payload: Dict[str, Any]
    chat: Optional[str] = None
    summary: Optional[str] = None
    timestamp: int

class CountResponse(BaseModel):
    count: int

class MultiDatabaseManager:
    """Manages connections to SQLite, PostgreSQL, and MongoDB"""
    
    def __init__(self):
        self.sqlite_db = None
        self.postgres_conn = None
        self.mongo_client = None
        self.mongo_db = None
        
        # Initialize databases
        self.init_sqlite()
        self.init_postgres()
        self.init_mongo()
    
    def init_sqlite(self):
        """Initialize SQLite database"""
        db_path = os.getenv('SQLITE_PATH', '/tmp/test.db')
        self.sqlite_db = sqlite3.connect(db_path, check_same_thread=False)
        self.sqlite_db.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_app TEXT NOT NULL,
                session_id TEXT NOT NULL,
                hook_event_type TEXT NOT NULL,
                payload TEXT,
                chat TEXT,
                summary TEXT,
                timestamp INTEGER NOT NULL
            )
        ''')
        self.sqlite_db.commit()
        print("✅ SQLite database initialized")
    
    def init_postgres(self):
        """Initialize PostgreSQL database"""
        if not HAS_POSTGRES:
            print("⚠️  PostgreSQL support not available (psycopg2 not installed)")
            return
        
        try:
            self.postgres_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', '5432')),
                database=os.getenv('POSTGRES_DB', 'testdb'),
                user=os.getenv('POSTGRES_USER', 'user'),
                password=os.getenv('POSTGRES_PASSWORD', 'password')
            )
            self.postgres_conn.autocommit = True
            
            # Create table if it doesn't exist
            cursor = self.postgres_conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    source_app VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    hook_event_type VARCHAR(255) NOT NULL,
                    payload JSONB,
                    chat TEXT,
                    summary TEXT,
                    timestamp BIGINT NOT NULL
                )
            ''')
            print("✅ PostgreSQL database initialized")
        except Exception as e:
            print(f"⚠️  PostgreSQL initialization failed: {e}")
            self.postgres_conn = None
    
    def init_mongo(self):
        """Initialize MongoDB database"""
        if not HAS_MONGO:
            print("⚠️  MongoDB support not available (pymongo not installed)")
            return
        
        try:
            # Try without authentication first
            self.mongo_client = MongoClient(
                host=os.getenv('MONGO_HOST', 'localhost'),
                port=int(os.getenv('MONGO_PORT', '27017')),
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            self.mongo_db = self.mongo_client[os.getenv('MONGO_DB', 'testdb')]
            
            # Test connection
            self.mongo_client.admin.command('ping')
            print("✅ MongoDB database initialized")
        except Exception as e:
            print(f"⚠️  MongoDB initialization failed: {e}")
            
            # Try with authentication if no-auth fails
            try:
                username = os.getenv('MONGO_USER')
                password = os.getenv('MONGO_PASSWORD')
                
                if username and password:
                    self.mongo_client = MongoClient(
                        host=os.getenv('MONGO_HOST', 'localhost'),
                        port=int(os.getenv('MONGO_PORT', '27017')),
                        username=username,
                        password=password,
                        authSource=os.getenv('MONGO_AUTH_DB', 'admin'),
                        serverSelectionTimeoutMS=5000
                    )
                    self.mongo_db = self.mongo_client[os.getenv('MONGO_DB', 'testdb')]
                    
                    # Test connection
                    self.mongo_client.admin.command('ping')
                    print("✅ MongoDB database initialized with authentication")
                else:
                    raise Exception("No authentication credentials provided")
            except Exception as auth_e:
                print(f"⚠️  MongoDB authentication also failed: {auth_e}")
                self.mongo_client = None
                self.mongo_db = None
    
    def insert_event(self, event: HookEvent) -> EventResponse:
        """Insert event into all available databases"""
        timestamp = event.timestamp or int(time.time() * 1000)
        event_id = None
        
        # Insert into SQLite
        if self.sqlite_db:
            cursor = self.sqlite_db.cursor()
            cursor.execute('''
                INSERT INTO events (source_app, session_id, hook_event_type, payload, chat, summary, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.source_app,
                event.session_id,
                event.hook_event_type,
                json.dumps(event.payload),
                event.chat,
                event.summary,
                timestamp
            ))
            event_id = cursor.lastrowid
            self.sqlite_db.commit()
        
        # Insert into PostgreSQL
        if self.postgres_conn:
            try:
                cursor = self.postgres_conn.cursor()
                cursor.execute('''
                    INSERT INTO events (source_app, session_id, hook_event_type, payload, chat, summary, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    event.source_app,
                    event.session_id,
                    event.hook_event_type,
                    json.dumps(event.payload),
                    event.chat,
                    event.summary,
                    timestamp
                ))
                if not event_id:
                    event_id = cursor.fetchone()[0]
            except Exception as e:
                print(f"⚠️  PostgreSQL insert failed: {e}")
        
        # Insert into MongoDB
        if self.mongo_db:
            try:
                doc = {
                    'source_app': event.source_app,
                    'session_id': event.session_id,
                    'hook_event_type': event.hook_event_type,
                    'payload': event.payload,
                    'chat': event.chat,
                    'summary': event.summary,
                    'timestamp': timestamp
                }
                self.mongo_db.events.insert_one(doc)
            except Exception as e:
                print(f"⚠️  MongoDB insert failed: {e}")
        
        return EventResponse(
            id=event_id or 1,
            source_app=event.source_app,
            session_id=event.session_id,
            hook_event_type=event.hook_event_type,
            payload=event.payload,
            chat=event.chat,
            summary=event.summary,
            timestamp=timestamp
        )
    
    def get_event_count(self) -> int:
        """Get total event count from SQLite"""
        if self.sqlite_db:
            cursor = self.sqlite_db.cursor()
            cursor.execute('SELECT COUNT(*) FROM events')
            return cursor.fetchone()[0]
        return 0
    
    def get_recent_events(self, limit: int = 100) -> List[EventResponse]:
        """Get recent events from SQLite"""
        if not self.sqlite_db:
            return []
        
        cursor = self.sqlite_db.cursor()
        cursor.execute('''
            SELECT id, source_app, session_id, hook_event_type, payload, chat, summary, timestamp
            FROM events
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        events = []
        for row in cursor.fetchall():
            events.append(EventResponse(
                id=row[0],
                source_app=row[1],
                session_id=row[2],
                hook_event_type=row[3],
                payload=json.loads(row[4]),
                chat=row[5],
                summary=row[6],
                timestamp=row[7]
            ))
        
        return events

# Create FastAPI app and database manager
app = FastAPI(title="Multi-Database Test Server", version="1.0.0")
db_manager = MultiDatabaseManager()

@app.get("/")
async def root():
    return "Multi-Agent Observability Server"

@app.post("/events")
async def create_event(event: HookEvent):
    """Create a new event"""
    try:
        saved_event = db_manager.insert_event(event)
        return saved_event.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

@app.get("/events/count")
async def get_event_count():
    """Get total event count"""
    count = db_manager.get_event_count()
    return {"count": count}

@app.get("/events/recent")
async def get_recent_events(limit: int = 100):
    """Get recent events"""
    events = db_manager.get_recent_events(limit)
    return [event.dict() for event in events]

@app.get("/events/filter-options")
async def get_filter_options():
    """Get filter options for events"""
    return {
        "source_apps": ["test_app", "another_app"],
        "session_ids": ["session-1", "session-2"],
        "hook_event_types": ["PreToolUse", "PostToolUse"]
    }

@app.options("/events")
async def events_options():
    """Handle OPTIONS requests for CORS"""
    return {
        "Allow": "GET, POST, OPTIONS",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }

if __name__ == "__main__":
    # Use the new config system with default port 8090
    port = int(os.getenv("PORT", "8090"))
    uvicorn.run(app, host="0.0.0.0", port=port)
