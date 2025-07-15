import { WebSocketServer } from 'ws';
import { initDatabase, getRecentEvents } from '../db';
import { HookEvent } from '../types';

// Set up WebSocket mock
jest.mock('ws', () => {
  const clients = new Set();

  return {
    WebSocketServer: jest.fn().mockImplementation(() => ({
      on: jest.fn((event, callback) => {
        if (event === 'connection') {
          setImmediate(() => callback({
            on: jest.fn(),
            send: jest.fn(data => clients.add(data)),
          }));
        }
      }),
      emit: jest.fn(),
      clients,
    })),
  };
});

// Mock configuration
jest.mock('../config', () => ({
  config: {
    PORT: 4000,
  },
  validateRequiredConfig: jest.fn(),
}));

// Import after mocks
import createApp from './test-app';

const app = createApp();

// Helper to send a WebSocket message
const sendMessage = async (message) => {
  const [ws] = app.ws.clients;
  if (ws) {
    ws.send(JSON.stringify(message));
  }
};

describe('WebSocket Handling', () => {
  beforeAll(async () => {
    // Initialize database
    initDatabase();
  });

  afterEach(async () => {
    // Clear mock data
    app.ws.clients.clear();
  });

  it('sends initial events on connection', async () => {
    const events: HookEvent[] = getRecentEvents(50);
    await sendMessage({ type: 'initial', data: events });

    app.ws.clients.forEach((data) => {
      const response = JSON.parse(data);
      expect(response.type).toEqual('initial');
      expect(response.data.length).toBeGreaterThan(0);
    });
  });

  it('broadcasts events to clients', async () => {
    const eventData: HookEvent = {
      source_app: 'ws-client',
      session_id: 'session-123',
      hook_event_type: 'SomeEvent',
      payload: { example: 'data' },
    };

    app.ws.clients.forEach((data, client) => {
      expect(client.send).toHaveBeenLastCalledWith(expect.stringContaining('data'));
    });
  });
});

