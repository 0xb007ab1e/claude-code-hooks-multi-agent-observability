import fs from 'fs';
import path from 'path';

// Test database path
const testDbPath = path.join(__dirname, 'test-events.db');

// Mock config before importing db functions
jest.mock('../config', () => ({
  config: {
    DATABASE_PATH: testDbPath,
  },
}));

import { initDatabase, insertEvent, getFilterOptions, getRecentEvents } from '../db';
import { HookEvent } from '../types';

describe('Database Functions', () => {
  beforeEach(() => {
    // Clean up test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
    
    initDatabase();
  });

  afterEach(() => {
    // Clean up test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  describe('insertEvent', () => {
    it('should insert a new event and return it with id and timestamp', () => {
      const event: HookEvent = {
        source_app: 'test-app',
        session_id: 'test-session',
        hook_event_type: 'test-event',
        payload: { data: 'test' },
      };

      const result = insertEvent(event);

      expect(result).toHaveProperty('id');
      expect(result).toHaveProperty('timestamp');
      expect(result.source_app).toBe('test-app');
      expect(result.session_id).toBe('test-session');
      expect(result.hook_event_type).toBe('test-event');
      expect(result.payload).toEqual({ data: 'test' });
    });

    it('should handle events with chat and summary', () => {
      const event: HookEvent = {
        source_app: 'test-app',
        session_id: 'test-session',
        hook_event_type: 'test-event',
        payload: { data: 'test' },
        chat: [{ role: 'user', content: 'Hello' }],
        summary: 'Test summary',
      };

      const result = insertEvent(event);

      expect(result.chat).toEqual([{ role: 'user', content: 'Hello' }]);
      expect(result.summary).toBe('Test summary');
    });
  });

  describe('getRecentEvents', () => {
    it('should return recent events in reverse chronological order', () => {
      const events = [
        {
          source_app: 'app1',
          session_id: 'session1',
          hook_event_type: 'event1',
          payload: { data: 'test1' },
        },
        {
          source_app: 'app2',
          session_id: 'session2',
          hook_event_type: 'event2',
          payload: { data: 'test2' },
        },
      ];

      events.forEach(event => insertEvent(event));

      const recentEvents = getRecentEvents(10);
      expect(recentEvents).toHaveLength(2);
      // Most recent event (app2) should be first
      expect(recentEvents[0].source_app).toBe('app2');
      expect(recentEvents[1].source_app).toBe('app1');
    });

    it('should respect the limit parameter', () => {
      const events = Array.from({ length: 5 }, (_, i) => ({
        source_app: `app${i}`,
        session_id: `session${i}`,
        hook_event_type: `event${i}`,
        payload: { data: `test${i}` },
      }));

      events.forEach(event => insertEvent(event));

      const recentEvents = getRecentEvents(3);
      expect(recentEvents).toHaveLength(3);
    });
  });

  describe('getFilterOptions', () => {
    it('should return filter options based on existing events', () => {
      const events = [
        {
          source_app: 'app1',
          session_id: 'session1',
          hook_event_type: 'event1',
          payload: { data: 'test1' },
        },
        {
          source_app: 'app2',
          session_id: 'session2',
          hook_event_type: 'event2',
          payload: { data: 'test2' },
        },
      ];

      events.forEach(event => insertEvent(event));

      const options = getFilterOptions();
      expect(options.source_apps).toContain('app1');
      expect(options.source_apps).toContain('app2');
      expect(options.session_ids).toContain('session1');
      expect(options.session_ids).toContain('session2');
      expect(options.hook_event_types).toContain('event1');
      expect(options.hook_event_types).toContain('event2');
    });
  });
});
