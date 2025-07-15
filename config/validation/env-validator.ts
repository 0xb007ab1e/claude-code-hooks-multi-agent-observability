/**
 * =============================================================================
 * ENVIRONMENT VARIABLES VALIDATION UTILITY
 * =============================================================================
 * This utility provides configuration validation that can be reused across
 * all stacks in the repository. It validates against the centralized schema
 * and provides consistent error reporting.
 * 
 * Usage:
 *   import { validateEnvironment } from './config/validation/env-validator';
 *   const config = validateEnvironment();
 * 
 * Author: Centralized Configuration Management System
 * =============================================================================
 */

import * as fs from 'fs';
import * as path from 'path';

// Define the environment variable schema
interface EnvSchema {
  [key: string]: {
    type: 'string' | 'number' | 'boolean';
    required?: boolean;
    enum?: string[];
    pattern?: RegExp;
    default?: string;
    description?: string;
  };
}

// Central environment schema definition
const ENV_SCHEMA: EnvSchema = {
  // API Keys
  ANTHROPIC_API_KEY: {
    type: 'string',
    required: true,
    description: 'Anthropic Claude API key'
  },
  OPENAI_API_KEY: {
    type: 'string',
    required: true,
    description: 'OpenAI API key'
  },
  ELEVENLABS_API_KEY: {
    type: 'string',
    required: true,
    description: 'ElevenLabs API key for text-to-speech'
  },

  // Model Configuration
  ANTHROPIC_MODEL: {
    type: 'string',
    default: 'claude-3-5-haiku-20241022',
    description: 'Default Anthropic model'
  },
  OPENAI_MODEL: {
    type: 'string',
    default: 'gpt-4.1-nano',
    description: 'Default OpenAI model'
  },
  OPENAI_TTS_MODEL: {
    type: 'string',
    default: 'gpt-4o-mini-tts',
    description: 'OpenAI TTS model'
  },
  OPENAI_TTS_VOICE: {
    type: 'string',
    default: 'nova',
    description: 'OpenAI TTS voice'
  },
  ELEVENLABS_MODEL: {
    type: 'string',
    default: 'eleven_turbo_v2_5',
    description: 'ElevenLabs model'
  },
  ELEVENLABS_VOICE_ID: {
    type: 'string',
    default: 'WejK3H1m7MI9CHnIjW9K',
    description: 'ElevenLabs voice ID'
  },

  // User Configuration
  ENGINEER_NAME: {
    type: 'string',
    default: 'Dan',
    description: 'Engineer/developer name for personalization'
  },

  // Server Configuration
  PORT: {
    type: 'number',
    required: true,
    pattern: /^\\d{1,5}$/,
    default: '4000',
    description: 'HTTP server port'
  },
  NODE_ENV: {
    type: 'string',
    required: true,
    enum: ['development', 'production', 'test'],
    default: 'development',
    description: 'Node.js environment'
  },
  GO_PORT: {
    type: 'number',
    default: '4001',
    description: 'Go server port'
  },
  PYTHON_PORT: {
    type: 'number',
    default: '4002',
    description: 'Python server port'
  },
  RUST_PORT: {
    type: 'number',
    default: '4003',
    description: 'Rust server port'
  },
  DOTNET_PORT: {
    type: 'number',
    default: '4004',
    description: '.NET server port'
  },

  // Database Configuration
  DATABASE_PATH: {
    type: 'string',
    default: 'events.db',
    description: 'SQLite database path'
  },
  POSTGRES_URL: {
    type: 'string',
    description: 'PostgreSQL connection URL'
  },
  DATABASE_URL: {
    type: 'string',
    description: 'Database connection URL'
  },
  DB_HOST: {
    type: 'string',
    default: 'localhost',
    description: 'Database host'
  },
  DB_PORT: {
    type: 'number',
    default: '5432',
    description: 'Database port'
  },
  DB_NAME: {
    type: 'string',
    default: 'observability',
    description: 'Database name'
  },
  DB_USER: {
    type: 'string',
    description: 'Database user'
  },
  DB_PASSWORD: {
    type: 'string',
    description: 'Database password'
  },

  // CORS Configuration
  CORS_ORIGINS: {
    type: 'string',
    default: '*',
    description: 'Comma-separated list of allowed CORS origins'
  },

  // Security
  API_KEY: {
    type: 'string',
    description: 'API key for authenticated requests'
  },
  JWT_SECRET: {
    type: 'string',
    description: 'JWT secret for token signing'
  },

  // Rate Limiting
  RATE_LIMIT_WINDOW_MS: {
    type: 'number',
    default: '900000',
    description: 'Rate limiting time window in milliseconds'
  },
  RATE_LIMIT_MAX_REQUESTS: {
    type: 'number',
    default: '100',
    description: 'Maximum requests per time window'
  },

  // WebSocket
  WS_HEARTBEAT_INTERVAL: {
    type: 'number',
    default: '30000',
    description: 'WebSocket heartbeat interval in milliseconds'
  },
  VITE_WEBSOCKET_URL: {
    type: 'string',
    default: 'ws://localhost:4000/stream',
    description: 'WebSocket server URL for client connections'
  },

  // Logging
  LOG_LEVEL: {
    type: 'string',
    enum: ['error', 'warn', 'info', 'debug'],
    default: 'info',
    description: 'Logging level'
  },
  CLAUDE_HOOKS_LOG_DIR: {
    type: 'string',
    default: 'logs',
    description: 'Claude hooks log directory'
  },

  // Client Configuration
  VITE_MAX_EVENTS_TO_DISPLAY: {
    type: 'number',
    default: '100',
    description: 'Maximum number of events to display in the client'
  },

  // Development Configuration
  DEV_MODE: {
    type: 'boolean',
    default: 'true',
    description: 'Development mode flag'
  },
  DEBUG_MODE: {
    type: 'boolean',
    default: 'false',
    description: 'Debug mode flag'
  },
  VERBOSE_LOGGING: {
    type: 'boolean',
    default: 'false',
    description: 'Verbose logging flag'
  },
  HOT_RELOAD: {
    type: 'boolean',
    default: 'true',
    description: 'Hot reload flag'
  },
  WATCH_FILES: {
    type: 'boolean',
    default: 'true',
    description: 'Watch files flag'
  }
};

// Validation result interface
interface ValidationResult {
  valid: boolean;
  config: Record<string, any>;
  errors: string[];
  warnings: string[];
}

// Helper function to convert string to appropriate type
function convertValue(value: string | undefined, type: string): any {
  if (value === undefined) return undefined;
  
  switch (type) {
    case 'number':
      const num = Number(value);
      return isNaN(num) ? value : num;
    case 'boolean':
      return value.toLowerCase() === 'true';
    case 'string':
    default:
      return value;
  }
}

// Helper function to validate a single environment variable
function validateEnvVar(key: string, value: string | undefined, schema: EnvSchema[string]): { valid: boolean; error?: string; warning?: string } {
  // Check if required and missing
  if (schema.required && (!value || value === '')) {
    return { valid: false, error: `Required environment variable ${key} is missing or empty` };
  }
  
  // If not required and missing, use default if available
  if (!value && schema.default !== undefined) {
    return { valid: true, warning: `Using default value for ${key}: ${schema.default}` };
  }
  
  // Skip validation if value is empty and not required
  if (!value && !schema.required) {
    return { valid: true };
  }
  
  // Validate enum values
  if (schema.enum && !schema.enum.includes(value!)) {
    return { valid: false, error: `Invalid value for ${key}. Expected one of: ${schema.enum.join(', ')}. Got: ${value}` };
  }
  
  // Validate pattern
  if (schema.pattern && !schema.pattern.test(value!)) {
    return { valid: false, error: `Invalid format for ${key}. Value: ${value}` };
  }
  
  return { valid: true };
}

// Main validation function
export function validateEnvironment(envVars: Record<string, string | undefined> = process.env): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    config: {},
    errors: [],
    warnings: []
  };
  
  // Validate each environment variable against the schema
  for (const [key, schema] of Object.entries(ENV_SCHEMA)) {
    const value = envVars[key];
    const validation = validateEnvVar(key, value, schema);
    
    if (!validation.valid) {
      result.valid = false;
      result.errors.push(validation.error!);
    } else {
      if (validation.warning) {
        result.warnings.push(validation.warning);
      }
      
      // Set the final value (use default if value is missing)
      const finalValue = value || schema.default;
      if (finalValue !== undefined) {
        result.config[key] = convertValue(finalValue, schema.type);
      }
    }
  }
  
  return result;
}

// Function to load and validate environment from .env file
export function loadAndValidateEnv(envFilePath?: string): ValidationResult {
  const repoRoot = path.resolve(__dirname, '../..');
  const envFile = envFilePath || path.join(repoRoot, '.env');
  
  // Try to load .env file if it exists
  if (fs.existsSync(envFile)) {
    const envContent = fs.readFileSync(envFile, 'utf8');
    const envVars: Record<string, string> = {};
    
    // Parse .env file
    envContent.split('\\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          let value = valueParts.join('=').trim();
          // Remove quotes if present
          value = value.replace(/^["']|["']$/g, '');
          envVars[key.trim()] = value;
        }
      }
    });
    
    // Merge with process.env (process.env takes precedence)
    const mergedEnv = { ...envVars, ...process.env };
    return validateEnvironment(mergedEnv);
  }
  
  // If no .env file, validate process.env
  return validateEnvironment();
}

// Function to print validation results
export function printValidationResults(result: ValidationResult): void {
  if (result.valid) {
    console.log('✅ Environment validation passed');
    
    if (result.warnings.length > 0) {
      console.log('⚠️  Warnings:');
      result.warnings.forEach(warning => console.log(`  - ${warning}`));
    }
  } else {
    console.error('❌ Environment validation failed');
    console.error('Errors:');
    result.errors.forEach(error => console.error(`  - ${error}`));
    
    if (result.warnings.length > 0) {
      console.log('⚠️  Warnings:');
      result.warnings.forEach(warning => console.log(`  - ${warning}`));
    }
  }
}

// Function to get typed configuration (for TypeScript projects)
export function getTypedConfig(): {
  anthropic: {
    apiKey: string;
    model: string;
  };
  openai: {
    apiKey: string;
    model: string;
    ttsModel: string;
    ttsVoice: string;
  };
  elevenlabs: {
    apiKey: string;
    model: string;
    voiceId: string;
  };
  server: {
    port: number;
    nodeEnv: string;
    corsOrigins: string;
  };
  database: {
    path: string;
    postgresUrl?: string;
    host: string;
    port: number;
    name: string;
    user?: string;
    password?: string;
  };
  logging: {
    level: string;
    logDir: string;
  };
  websocket: {
    heartbeatInterval: number;
    url: string;
  };
  client: {
    maxEvents: number;
  };
  rateLimiting: {
    windowMs: number;
    maxRequests: number;
  };
  security: {
    apiKey?: string;
    jwtSecret?: string;
  };
  development: {
    devMode: boolean;
    debugMode: boolean;
    verboseLogging: boolean;
    hotReload: boolean;
    watchFiles: boolean;
  };
} {
  const result = validateEnvironment();
  
  if (!result.valid) {
    printValidationResults(result);
    throw new Error('Environment validation failed');
  }
  
  const config = result.config;
  
  return {
    anthropic: {
      apiKey: config.ANTHROPIC_API_KEY,
      model: config.ANTHROPIC_MODEL
    },
    openai: {
      apiKey: config.OPENAI_API_KEY,
      model: config.OPENAI_MODEL,
      ttsModel: config.OPENAI_TTS_MODEL,
      ttsVoice: config.OPENAI_TTS_VOICE
    },
    elevenlabs: {
      apiKey: config.ELEVENLABS_API_KEY,
      model: config.ELEVENLABS_MODEL,
      voiceId: config.ELEVENLABS_VOICE_ID
    },
    server: {
      port: config.PORT,
      nodeEnv: config.NODE_ENV,
      corsOrigins: config.CORS_ORIGINS
    },
    database: {
      path: config.DATABASE_PATH,
      postgresUrl: config.POSTGRES_URL,
      host: config.DB_HOST,
      port: config.DB_PORT,
      name: config.DB_NAME,
      user: config.DB_USER,
      password: config.DB_PASSWORD
    },
    logging: {
      level: config.LOG_LEVEL,
      logDir: config.CLAUDE_HOOKS_LOG_DIR
    },
    websocket: {
      heartbeatInterval: config.WS_HEARTBEAT_INTERVAL,
      url: config.VITE_WEBSOCKET_URL
    },
    client: {
      maxEvents: config.VITE_MAX_EVENTS_TO_DISPLAY
    },
    rateLimiting: {
      windowMs: config.RATE_LIMIT_WINDOW_MS,
      maxRequests: config.RATE_LIMIT_MAX_REQUESTS
    },
    security: {
      apiKey: config.API_KEY,
      jwtSecret: config.JWT_SECRET
    },
    development: {
      devMode: config.DEV_MODE,
      debugMode: config.DEBUG_MODE,
      verboseLogging: config.VERBOSE_LOGGING,
      hotReload: config.HOT_RELOAD,
      watchFiles: config.WATCH_FILES
    }
  };
}

// Export the schema for use in other languages
export { ENV_SCHEMA };
