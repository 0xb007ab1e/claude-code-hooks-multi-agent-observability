import { z } from 'zod';

// Define the configuration schema
const configSchema = z.object({
  // Server configuration
  PORT: z.coerce.number().min(1).max(65535).default(8090),
  
  // Database configuration
  DATABASE_PATH: z.string().min(1).default('events.db'),
  
  // CORS configuration
  CORS_ORIGINS: z
    .string()
    .default('*')
    .transform((val) => val === '*' ? ['*'] : val.split(',').map(s => s.trim())),
  
  // Optional: Future PostgreSQL support
  POSTGRES_URL: z.string().optional(),
  
  // Alternative database connection variables
  DATABASE_URL: z.string().optional(),
  DB_PASSWORD: z.string().optional(),
  DB_HOST: z.string().optional(),
  DB_PORT: z.coerce.number().optional(),
  DB_NAME: z.string().optional(),
  DB_USER: z.string().optional(),
  
  // Optional: Authentication/API keys
  API_KEY: z.string().optional(),
  JWT_SECRET: z.string().optional(),
  
  // Optional: Rate limiting
  RATE_LIMIT_WINDOW_MS: z.coerce.number().default(900000), // 15 minutes
  RATE_LIMIT_MAX_REQUESTS: z.coerce.number().default(100),
  
  // Optional: WebSocket configuration
  WS_HEARTBEAT_INTERVAL: z.coerce.number().default(30000), // 30 seconds
  
  // Optional: Logging level
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  
  // Environment
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development')
});

// Type inference from schema
export type Config = z.infer<typeof configSchema>;

// Load and validate configuration
function loadConfig(): Config {
  try {
    const config = configSchema.parse({
      PORT: process.env.PORT,
      DATABASE_PATH: process.env.DATABASE_PATH,
      CORS_ORIGINS: process.env.CORS_ORIGINS,
      POSTGRES_URL: process.env.POSTGRES_URL,
      DATABASE_URL: process.env.DATABASE_URL,
      DB_PASSWORD: process.env.DB_PASSWORD,
      DB_HOST: process.env.DB_HOST,
      DB_PORT: process.env.DB_PORT,
      DB_NAME: process.env.DB_NAME,
      DB_USER: process.env.DB_USER,
      API_KEY: process.env.API_KEY,
      JWT_SECRET: process.env.JWT_SECRET,
      RATE_LIMIT_WINDOW_MS: process.env.RATE_LIMIT_WINDOW_MS,
      RATE_LIMIT_MAX_REQUESTS: process.env.RATE_LIMIT_MAX_REQUESTS,
      WS_HEARTBEAT_INTERVAL: process.env.WS_HEARTBEAT_INTERVAL,
      LOG_LEVEL: process.env.LOG_LEVEL,
      NODE_ENV: process.env.NODE_ENV
    });
    
    return config;
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('❌ Configuration validation failed:');
      error.issues.forEach((err) => {
        console.error(`  - ${err.path.join('.')}: ${err.message}`);
      });
      console.error('\nPlease check your environment variables and try again.');
      console.error('See .env.sample for required configuration options.');
    } else {
      console.error('❌ Failed to load configuration:', error);
    }
    process.exit(1);
  }
}

// Export the validated configuration
export const config = loadConfig();

// Helper function to validate required environment variables on startup
export function validateRequiredConfig(): void {
  const requiredInProduction = ['DATABASE_PATH'];
  
  if (config.NODE_ENV === 'production') {
    for (const key of requiredInProduction) {
      if (!process.env[key]) {
        console.error(`❌ Missing required environment variable: ${key}`);
        process.exit(1);
      }
    }
  }
  
  console.log('✅ Configuration loaded successfully');
  console.log(`📦 Environment: ${config.NODE_ENV}`);
  console.log(`🚀 Server will run on port: ${config.PORT}`);
  console.log(`💾 Database path: ${config.DATABASE_PATH}`);
  console.log(`🌐 CORS origins: ${Array.isArray(config.CORS_ORIGINS) ? config.CORS_ORIGINS.join(', ') : config.CORS_ORIGINS}`);
}
