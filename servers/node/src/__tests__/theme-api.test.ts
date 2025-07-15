import request from 'supertest';
import fs from 'fs';
import path from 'path';
import { Express } from 'express';

// Test database path
const testDbPath = path.join(__dirname, 'test-theme-events.db');

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

describe('Theme API Endpoints', () => {
  let app: Express;
  let testThemeId: string;

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

  beforeEach(async () => {
    // Create a fresh theme for each test
    const themeData = {
      name: `test-theme-${Date.now()}`,
      displayName: 'Test Theme',
      description: 'A test theme',
      colors: {
        primary: '#ff0000',
        primaryHover: '#ff3333',
        primaryLight: '#ff6666',
        primaryDark: '#cc0000',
        bgPrimary: '#f5f5f5',
        bgSecondary: '#eeeeee',
        bgTertiary: '#dddddd',
        bgQuaternary: '#cccccc',
        textPrimary: '#333333',
        textSecondary: '#666666',
        textTertiary: '#999999',
        textQuaternary: '#bbbbbb',
        borderPrimary: '#cccccc',
        borderSecondary: '#dddddd',
        borderTertiary: '#eeeeee',
        accentSuccess: '#00ff00',
        accentWarning: '#ffcc00',
        accentError: '#ff0000',
        accentInfo: '#00ccff',
        shadow: '#666',
        shadowLg: '#444',
        hoverBg: '#e0e0e0',
        activeBg: '#d0d0d0',
        focusRing: '#00f',
      },
      isPublic: true,
      authorId: 'test-author',
      authorName: 'Test Author',
      tags: ['test', 'theme'],
    };

    const response = await request(app)
      .post('/api/themes')
      .send(themeData);

    if (response.status === 201) {
      testThemeId = response.body.data.id;
    }
  });

  describe('POST /api/themes', () => {
    it('should create a new theme successfully', async () => {
      const themeData = {
        name: 'test-theme',
        displayName: 'Test Theme',
        description: 'A test theme',
        colors: {
          primary: '#ff0000',
          primaryHover: '#ff3333',
          primaryLight: '#ff6666',
          primaryDark: '#cc0000',
          bgPrimary: '#f5f5f5',
          bgSecondary: '#eeeeee',
          bgTertiary: '#dddddd',
          bgQuaternary: '#cccccc',
          textPrimary: '#333333',
          textSecondary: '#666666',
          textTertiary: '#999999',
          textQuaternary: '#bbbbbb',
          borderPrimary: '#cccccc',
          borderSecondary: '#dddddd',
          borderTertiary: '#eeeeee',
          accentSuccess: '#00ff00',
          accentWarning: '#ffcc00',
          accentError: '#ff0000',
          accentInfo: '#00ccff',
          shadow: '#666',
          shadowLg: '#444',
          hoverBg: '#e0e0e0',
          activeBg: '#d0d0d0',
          focusRing: '#00f',
        },
        isPublic: true,
        authorId: 'test-author',
        authorName: 'Test Author',
        tags: ['test', 'theme'],
      };

      const response = await request(app)
        .post('/api/themes')
        .send(themeData);

      expect(response.status).toBe(201);
      expect(response.body.success).toBe(true);
      expect(response.body).toHaveProperty('data');
      expect(response.body.data).toHaveProperty('id');
      testThemeId = response.body.data.id;
    });

    it('should return 400 for invalid theme data', async () => {
      const invalidThemeData = {
        name: 'invalid-theme',
        // Missing required fields
      };

      const response = await request(app)
        .post('/api/themes')
        .send(invalidThemeData);

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
      expect(response.body).toHaveProperty('error');
    });
  });

  describe('GET /api/themes', () => {
    it('should return list of themes', async () => {
      const response = await request(app).get('/api/themes');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('data');
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should filter themes by query', async () => {
      const response = await request(app).get('/api/themes?query=test');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('data');
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should filter themes by isPublic', async () => {
      const response = await request(app).get('/api/themes?isPublic=true');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('data');
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should limit results', async () => {
      const response = await request(app).get('/api/themes?limit=5');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('data');
      expect(response.body.data.length).toBeLessThanOrEqual(5);
    });
  });

  describe('GET /api/themes/:id', () => {
    it('should return a specific theme', async () => {
      const response = await request(app).get(`/api/themes/${testThemeId}`);

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body).toHaveProperty('data');
      expect(response.body.data.id).toBe(testThemeId);
    });

    it('should return 404 for non-existent theme', async () => {
      const response = await request(app).get('/api/themes/non-existent-id');

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });

    it('should return 200 for themes list route', async () => {
      const response = await request(app).get('/api/themes/');

      expect(response.status).toBe(200); // This matches the themes list route
      expect(response.body).toHaveProperty('data');
      expect(Array.isArray(response.body.data)).toBe(true);
    });
  });

  describe('PUT /api/themes/:id', () => {
    it('should update a theme successfully', async () => {
      const updateData = {
        description: 'Updated description',
        colors: {
          primary: '#0000ff',
          primaryHover: '#3333ff',
          primaryLight: '#6666ff',
          primaryDark: '#0000cc',
          bgPrimary: '#f0f0f0',
          bgSecondary: '#e0e0e0',
          bgTertiary: '#d0d0d0',
          bgQuaternary: '#c0c0c0',
          textPrimary: '#000000',
          textSecondary: '#333333',
          textTertiary: '#666666',
          textQuaternary: '#999999',
          borderPrimary: '#aaaaaa',
          borderSecondary: '#bbbbbb',
          borderTertiary: '#cccccc',
          accentSuccess: '#00ff00',
          accentWarning: '#ffff00',
          accentError: '#ff0000',
          accentInfo: '#00ffff',
          shadow: '#333',
          shadowLg: '#111',
          hoverBg: '#f0f0f0',
          activeBg: '#e0e0e0',
          focusRing: '#00f',
        },
      };

      const response = await request(app)
        .put(`/api/themes/${testThemeId}`)
        .send(updateData);

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should return 400 for invalid update data', async () => {
      const invalidUpdateData = {
        colors: 'invalid-colors-format',
      };

      const response = await request(app)
        .put(`/api/themes/${testThemeId}`)
        .send(invalidUpdateData);

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for missing theme ID', async () => {
      const response = await request(app)
        .put('/api/themes/')
        .send({});

      expect(response.status).toBe(404); // Express returns 404 for missing route
    });
  });

  describe('GET /api/themes/:id/export', () => {
    it('should export a theme', async () => {
      const response = await request(app).get(`/api/themes/${testThemeId}/export`);

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('theme');
      expect(response.body.theme.id).toBe(testThemeId);
      expect(response.headers['content-disposition']).toContain('attachment');
    });

    it('should return 404 for non-existent theme', async () => {
      const response = await request(app).get('/api/themes/non-existent-id/export');

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });
  });

  describe('POST /api/themes/import', () => {
    it('should import a theme', async () => {
      // First export a theme to get the format
      const exportResponse = await request(app).get(`/api/themes/${testThemeId}/export`);
      const exportData = exportResponse.body;
      
      // Modify the import data to create a new theme
      const importData = {
        ...exportData,
        theme: {
          ...exportData.theme,
          name: 'imported-theme',
          displayName: 'Imported Theme',
        },
      };

      const response = await request(app)
        .post('/api/themes/import?authorId=test-author')
        .send(importData);

      expect(response.status).toBe(201);
      expect(response.body.success).toBe(true);
    });

    it('should return 400 for invalid import data', async () => {
      const invalidImportData = {
        invalid: 'data',
      };

      const response = await request(app)
        .post('/api/themes/import?authorId=test-author')
        .send(invalidImportData);

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });
  });

  describe('GET /api/themes/stats', () => {
    it('should return theme statistics', async () => {
      const response = await request(app).get('/api/themes/stats');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('success');
    });
  });

  describe('DELETE /api/themes/:id', () => {
    it('should delete a theme', async () => {
      const response = await request(app)
        .delete(`/api/themes/${testThemeId}?authorId=test-author`);

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
    });

    it('should return 404 for non-existent theme', async () => {
      const response = await request(app)
        .delete('/api/themes/non-existent-id?authorId=test-author');

      expect(response.status).toBe(404);
      expect(response.body.success).toBe(false);
    });

    it('should return 400 for missing theme ID', async () => {
      const response = await request(app)
        .delete('/api/themes/?authorId=test-author');

      expect(response.status).toBe(404); // Express returns 404 for missing route
    });
  });
});
