import express from 'express';
import { WebSocketServer } from 'ws';
import { config, validateRequiredConfig } from './config.js';
import { initDatabase, insertEvent, getFilterOptions, getRecentEvents, getEventCount } from './db.js';
import type { HookEvent } from './types.js';
import {
  createTheme,
  updateThemeById,
  getThemeById,
  searchThemes,
  deleteThemeById,
  exportThemeById,
  importTheme,
  getThemeStats
} from './theme.js';
import helmet from 'helmet';
import cors from 'cors';
import morgan from 'morgan';
import compression from 'compression';
import winston from 'winston';

const isTestMode = process.argv.includes('--test');

// Initialize Winston logger
function createLogger(enableInteractiveLogging: boolean = true, testMode: boolean = false) {
  const logLevel = testMode ? (process.env.TEST_LOG_LEVEL || 'error') : config.LOG_LEVEL;
  
  const transports = [];
  
  if (enableInteractiveLogging) {
    transports.push(new winston.transports.Console({
      format: winston.format.simple(),
    }));
  } else if (testMode) {
    // In test mode without interactive logging, still log errors to console
    transports.push(new winston.transports.Console({
      level: 'error',
      format: winston.format.simple(),
    }));
  }
  
  const logger = winston.createLogger({
    level: logLevel,
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.json()
    ),
    transports
  });
  
  return logger;
}

// Create server factory function
export function createServer(options: { enableInteractiveLogging?: boolean, port?: number, testMode?: boolean } = {}) {
  const { enableInteractiveLogging = true, port = config.PORT, testMode = false } = options;
  const logger = createLogger(enableInteractiveLogging, testMode);
  
  // Create a stream object for Morgan
  const morganStream = {
    write: (message: string) => {
      if (enableInteractiveLogging) {
        logger.info(message.trim());
      }
    }
  };

  // Initialize Express app
  const app = express();
  app.use(express.json());
  app.use(helmet());
  
  // Handle OPTIONS requests before CORS middleware
  app.options('/events', (req, res) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET,HEAD,PUT,PATCH,POST,DELETE');
    res.header('Access-Control-Allow-Headers', 'Content-Type,Authorization');
    res.status(200).end();
  });
  
  app.use(cors({ 
    origin: config.CORS_ORIGINS,
    optionsSuccessStatus: 200
  }));
  app.use(compression());
  
  // Only add Morgan logging if interactive logging is enabled
  if (enableInteractiveLogging) {
    app.use(morgan('combined', { stream: morganStream }));
  }

  // Error handler for malformed JSON
  app.use((err: any, req: any, res: any, next: any) => {
    if (err instanceof SyntaxError && (err as any).status === 400 && 'body' in err) {
      return res.status(400).json({ error: 'Invalid request', message: 'Malformed JSON' });
    }
    next(err);
  });

  // Validate configuration and initialize database
  validateRequiredConfig();
  initDatabase();

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
      logger.error('Error processing event:', error);
      if (error instanceof SyntaxError) {
        res.status(400).json({ error: 'Invalid request', message: 'Malformed JSON' });
      } else {
        res.status(400).json({ error: 'Invalid request', message: (error as Error).message || 'Unknown error' });
      }
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

  app.get('/events/count', (req, res) => {
    const count = getEventCount();
    res.json({ count });
  });


  // Theme API endpoints

  // POST /api/themes - Create a new theme
  app.post('/api/themes', async (req, res) => {
    try {
      const result = await createTheme(req.body);
      const status = result.success ? 201 : 400;
      
      // Transform response to match test expectations
      if (result.success && result.data) {
        res.status(status).json({
          success: result.success,
          id: result.data.id,
          message: result.message
        });
      } else {
        res.status(status).json(result);
      }
    } catch (error) {
      logger.error('Error creating theme:', error);
      res.status(400).json({ 
        success: false, 
        error: 'Invalid request body' 
      });
    }
  });

  // GET /api/themes/stats - Get theme statistics
  app.get('/api/themes/stats', async (req, res) => {
    const result = await getThemeStats();
    res.json(result);
  });

  // GET /api/themes - Search themes
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
    
    // Transform response to match test expectations
    if (result.success) {
      res.json({
        success: result.success,
        themes: result.data
      });
    } else {
      res.status(400).json(result);
    }
  });

  // GET /api/themes/:id - Get a specific theme
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
    
    // Transform response to match test expectations
    if (result.success) {
      res.status(status).json({
        success: result.success,
        theme: result.data
      });
    } else {
      res.status(status).json(result);
    }
  });

  // PUT /api/themes/:id - Update a theme
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
      logger.error('Error updating theme:', error);
      res.status(400).json({ 
        success: false, 
        error: 'Invalid request body' 
      });
    }
  });

  // DELETE /api/themes/:id - Delete a theme
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

  // GET /api/themes/:id/export - Export a theme
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

  // POST /api/themes/import - Import a theme
  app.post('/api/themes/import', async (req, res) => {
    try {
      const authorId = req.query.authorId as string || undefined;
      const result = await importTheme(req.body, authorId);
      
      const status = result.success ? 201 : 400;
      res.status(status).json(result);
    } catch (error) {
      logger.error('Error importing theme:', error);
      res.status(400).json({ 
        success: false, 
        error: 'Invalid import data' 
      });
    }
  });


  // Health check endpoint
  app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
  });

  // Default route
  app.get('/', (req, res) => {
    res.send('Multi-Agent Observability Server');
  });

  // Catch-all handler for unsupported methods
  app.use('*', (req, res) => {
    res.status(200).send('Multi-Agent Observability Server');
  });

  // WebSocket setup
  const wss = new WebSocketServer({ noServer: true });
  const wsClients = new Set<any>();

  wss.on('connection', (ws) => {
    wsClients.add(ws);
    logger.info('WebSocket client connected');
    ws.send(JSON.stringify({ type: 'initial', data: getRecentEvents(50) }));
    ws.on('close', () => {
      wsClients.delete(ws);
      logger.info('WebSocket client disconnected');
    });
    ws.on('message', (message) => {
      logger.info(`Received message: ${message}`);
    });
  });

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

  // Create HTTP server and handle WebSocket upgrade
  const server = app.listen(port, () => {
    logger.info(`Server running on http://localhost:${port}`);
    logger.info(`WebSocket endpoint: ws://localhost:${port}/stream`);
  });

  server.on('upgrade', (request, socket, head) => {
    const pathname = new URL(request.url || '', 'http://localhost').pathname;
    if (pathname === '/stream') {
      wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request);
      });
    } else {
      socket.write('HTTP/1.1 405 Method Not Allowed\r\n\r\n');
      socket.destroy();
    }
  });

  // Graceful shutdown
  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);

  function shutdown() {
    logger.info('Shutting down server...');
    server.close(() => {
      logger.info('HTTP server closed');
      process.exit(0);
    });
    setTimeout(() => {
      logger.warn('Forcing shutdown');
      process.exit(1);
    }, 10000);
  }

  return server;
}

// If called directly, start the server
if (import.meta.url === `file://${process.argv[1]}`) {
  if (isTestMode) {
    // Start in test mode - interactive logging controlled by ENABLE_LOGGING env var
    const port = process.env.PORT || 8090;
  const enableInteractiveLogging = process.env.ENABLE_LOGGING === 'true';
  createServer({
      enableInteractiveLogging,
      port: Number(port),
      testMode: true
    });
  } else {
    // Start in normal mode
    createServer();
  }
}
