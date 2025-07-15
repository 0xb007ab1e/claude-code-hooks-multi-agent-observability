import express from 'express';
import { WebSocketServer } from 'ws';
import { initDatabase, insertEvent, getFilterOptions, getRecentEvents } from '../db';
import type { HookEvent } from '../types';
import {
  createTheme,
  updateThemeById,
  getThemeById,
  searchThemes,
  deleteThemeById,
  exportThemeById,
  importTheme,
  getThemeStats
} from '../theme';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';

export default function createApp() {
  const app = express();
  
  // Basic middleware
  app.use(express.json());
  app.use(helmet());
  app.use(cors());
  app.use(compression());

  // Initialize database
  initDatabase();

  // WebSocket clients tracking
  const wsClients = new Set<any>();

  // Function to broadcast to WebSocket clients
  function broadcastToWebSocketClients(message: any) {
    const data = JSON.stringify(message);
    wsClients.forEach((client) => {
      if (client.readyState === 1) {
        client.send(data);
      } else {
        wsClients.delete(client);
      }
    });
  }

  // HTTP endpoints
  app.post('/events', (req, res) => {
    try {
      const event: HookEvent = req.body;
      if (!event.source_app || !event.session_id || !event.hook_event_type || !event.payload) {
        return res.status(400).json({ error: 'Missing required fields' });
      }
      const savedEvent = insertEvent(event);
      broadcastToWebSocketClients({ type: 'event', data: savedEvent });
      res.json(savedEvent);
    } catch (error) {
      res.status(400).json({ error: 'Invalid request' });
    }
  });

  app.get('/events/filter-options', (req, res) => {
    const options = getFilterOptions();
    res.json(options);
  });

  app.get('/events/recent', (req, res) => {
    const limit = parseInt(req.query.limit as string) || 100;
    const events = getRecentEvents(limit);
    res.json(events);
  });

  // Theme API endpoints
  app.post('/api/themes', async (req, res) => {
    try {
      const result = await createTheme(req.body);
      const status = result.success ? 201 : 400;
      res.status(status).json(result);
    } catch (error) {
      res.status(400).json({ 
        success: false, 
        error: 'Invalid request body' 
      });
    }
  });

  app.get('/api/themes', async (req, res) => {
    const query = {
      query: req.query.query as string || undefined,
      isPublic: req.query.isPublic ? req.query.isPublic === 'true' : undefined,
      authorId: req.query.authorId as string || undefined,
      sortBy: req.query.sortBy as any || undefined,
      sortOrder: req.query.sortOrder as any || undefined,
      limit: req.query.limit ? parseInt(req.query.limit as string) : undefined,
      offset: req.query.offset ? parseInt(req.query.offset as string) : undefined,
    };
    
    const result = await searchThemes(query);
    res.json(result);
  });

  // Stats route must come before the :id route to avoid parameter conflicts
  app.get('/api/themes/stats', async (req, res) => {
    const result = await getThemeStats();
    res.json(result);
  });

  app.get('/api/themes/:id', async (req, res) => {
    const { id } = req.params;
    if (!id) {
      return res.status(400).json({ 
        success: false, 
        error: 'Theme ID is required' 
      });
    }
    
    const result = await getThemeById(id);
    const status = result.success ? 200 : 404;
    res.status(status).json(result);
  });

  app.put('/api/themes/:id', async (req, res) => {
    const { id } = req.params;
    if (!id) {
      return res.status(400).json({ 
        success: false, 
        error: 'Theme ID is required' 
      });
    }
    
    try {
      const result = await updateThemeById(id, req.body);
      const status = result.success ? 200 : 400;
      res.status(status).json(result);
    } catch (error) {
      res.status(400).json({ 
        success: false, 
        error: 'Invalid request body' 
      });
    }
  });

  app.delete('/api/themes/:id', async (req, res) => {
    const { id } = req.params;
    if (!id) {
      return res.status(400).json({ 
        success: false, 
        error: 'Theme ID is required' 
      });
    }
    
    const authorId = req.query.authorId as string || undefined;
    const result = await deleteThemeById(id, authorId);
    
    const status = result.success ? 200 : (result.error?.includes('not found') ? 404 : 403);
    res.status(status).json(result);
  });

  app.get('/api/themes/:id/export', async (req, res) => {
    const { id } = req.params;
    
    if (!id) {
      return res.status(400).json({ 
        success: false, 
        error: 'Theme ID is required' 
      });
    }
    
    const result = await exportThemeById(id);
    if (!result.success) {
      const status = result.error?.includes('not found') ? 404 : 400;
      return res.status(status).json(result);
    }
    
    res.setHeader('Content-Disposition', `attachment; filename="${result.data.theme.name}.json"`);
    res.json(result.data);
  });

  app.post('/api/themes/import', async (req, res) => {
    try {
      const authorId = req.query.authorId as string || undefined;
      const result = await importTheme(req.body, authorId);
      
      const status = result.success ? 201 : 400;
      res.status(status).json(result);
    } catch (error) {
      res.status(400).json({ 
        success: false, 
        error: 'Invalid import data' 
      });
    }
  });

  // Default route
  app.get('/', (req, res) => {
    res.send('Multi-Agent Observability Server');
  });

  // Mock WebSocket server for testing
  const wss = new WebSocketServer({ noServer: true });
  
  wss.on('connection', (ws) => {
    wsClients.add(ws);
    ws.send(JSON.stringify({ type: 'initial', data: getRecentEvents(50) }));
    ws.on('close', () => {
      wsClients.delete(ws);
    });
  });

  // Add ws property to app for test access
  (app as any).ws = wss;
  (app as any).wsClients = wsClients;

  return app;
}
