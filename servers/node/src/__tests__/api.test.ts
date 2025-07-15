import request from 'supertest';
import fs from 'fs';
import path from 'path';
import { Express } from 'express';

// Test database path
const testDbPath = path.join(__dirname, 'test-api-events.db');

// Mock config before importing app
jest.mock('../config', () => ({
  config: {
    DATABASE_PATH: testDbPath,
    PORT: 4000,
    LOG_LEVEL: 'error',
    CORS_ORIGINS: ['http://localhost:3000'],
  },
  validateRequiredConfig: jest.fn(),
}));

// Mock Winston logger to avoid console output during tests
jest.mock('winston', () => ({
  createLogger: jest.fn().mockReturnValue({
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
  }),
  format: {
    combine: jest.fn(),
    timestamp: jest.fn(),
    json: jest.fn(),
    simple: jest.fn(),
  },
  transports: {
    Console: jest.fn(),
  },
}));

// Import after mocking
import { initDatabase } from '../db';

describe('API Endpoints', () => {
  let app: Express;
  
  beforeAll(async () => {
    // Clean up test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
    
    initDatabase();
    
    // Import app after database is initialized
    const { default: createApp } = await import('./test-app');
    app = createApp();
  });

  afterAll(() => {
    // Clean up test database
    if (fs.existsSync(testDbPath)) {
      fs.unlinkSync(testDbPath);
    }
  });

  describe('GET /', () => {
    it('should return welcome message', async () => {
      const response = await request(app).get('/');
      expect(response.status).toBe(200);
      expect(response.text).toBe('Multi-Agent Observability Server');
    });
  });

  describe('POST /events', () => {
    it('should create a new event successfully', async () => {
      const eventData = {
        source_app: 'test-app',
        session_id: 'test-session-123',
        hook_event_type: 'PreToolUse',
        payload: { tool: 'Bash', command: 'ls -la' },
      };

      const response = await request(app)
        .post('/events')
        .send(eventData);

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('id');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body.source_app).toBe('test-app');
      expect(response.body.session_id).toBe('test-session-123');
      expect(response.body.hook_event_type).toBe('PreToolUse');
      expect(response.body.payload).toEqual({ tool: 'Bash', command: 'ls -la' });
    });

    it('should handle events with chat and summary', async () => {
      const eventData = {
        source_app: 'test-app',
        session_id: 'test-session-456',
        hook_event_type: 'PostToolUse',
        payload: { tool: 'Bash', result: 'success' },
        chat: [{ role: 'user', content: 'List files' }],
        summary: 'User requested file listing',
      };

      const response = await request(app)
        .post('/events')
        .send(eventData);

      expect(response.status).toBe(200);
      expect(response.body.chat).toEqual([{ role: 'user', content: 'List files' }]);
      expect(response.body.summary).toBe('User requested file listing');
    });

    it('should return 400 for missing required fields', async () => {
      const invalidEventData = {
        source_app: 'test-app',
        // Missing required fields
      };

      const response = await request(app)
        .post('/events')
        .send(invalidEventData);

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toBe('Missing required fields');
    });

    it('should return 400 for invalid JSON', async () => {
      const response = await request(app)
        .post('/events')
        .send('invalid json');

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty('error');
    });
  });

  describe('GET /events/recent', () => {
    beforeEach(async () => {
      // Add some test events
      await request(app)
        .post('/events')
        .send({
          source_app: 'app1',
          session_id: 'session1',
          hook_event_type: 'event1',
          payload: { data: 'test1' },
        });

      await request(app)
        .post('/events')
        .send({
          source_app: 'app2',
          session_id: 'session2',
          hook_event_type: 'event2',
          payload: { data: 'test2' },
        });
    });

    it('should return recent events', async () => {
      const response = await request(app).get('/events/recent');
      
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body.length).toBeGreaterThan(0);
    });

    it('should respect limit parameter', async () => {
      const response = await request(app).get('/events/recent?limit=1');
      
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body.length).toBe(1);
    });

    it('should default to 100 limit if not specified', async () => {
      const response = await request(app).get('/events/recent');
      
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body)).toBe(true);
      // Should not exceed 100 items
      expect(response.body.length).toBeLessThanOrEqual(100);
    });
  });

  describe('GET /events/filter-options', () => {
    it('should return filter options', async () => {
      const response = await request(app).get('/events/filter-options');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('source_apps');
      expect(response.body).toHaveProperty('session_ids');
      expect(response.body).toHaveProperty('hook_event_types');
      expect(Array.isArray(response.body.source_apps)).toBe(true);
      expect(Array.isArray(response.body.session_ids)).toBe(true);
      expect(Array.isArray(response.body.hook_event_types)).toBe(true);
    });
  });
});
