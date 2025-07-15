# Test Mode Configuration

The Node.js server supports a test mode that can be activated using the `--test` CLI flag. This mode is designed to be used in testing environments where you want to run the server without verbose logging.

## Usage

### Basic Test Mode (No Interactive Logging)
```bash
npm run start:test
# or
node dist/index.js --test
```

### Test Mode with Interactive Logging
```bash
ENABLE_LOGGING=true npm run start:test
# or
ENABLE_LOGGING=true node dist/index.js --test
```

### Test Mode with Custom Log Level
```bash
TEST_LOG_LEVEL=info npm run start:test
# or
TEST_LOG_LEVEL=warn ENABLE_LOGGING=true npm run start:test
```

## Environment Variables

### `ENABLE_LOGGING`
- **Default**: `false` (in test mode)
- **Values**: `true` | `false`
- **Description**: Controls whether interactive logging is enabled in test mode. When set to `true`, full logging including HTTP requests will be displayed.

### `TEST_LOG_LEVEL`
- **Default**: `error`
- **Values**: `error` | `warn` | `info` | `debug`
- **Description**: Sets the logging level when in test mode. This only affects what gets logged to the console.

### `PORT`
- **Default**: `4000`
- **Values**: Any valid port number
- **Description**: Port number for the server to bind to.

## Logging Behavior

### Test Mode (Default)
- **Interactive Logging**: Disabled
- **HTTP Request Logging**: Disabled (no Morgan middleware)
- **Error Logging**: Enabled (errors are still logged to console)
- **Log Level**: `error` (or `TEST_LOG_LEVEL` if set)

### Test Mode with `ENABLE_LOGGING=true`
- **Interactive Logging**: Enabled
- **HTTP Request Logging**: Enabled (Morgan middleware active)
- **Error Logging**: Enabled
- **Log Level**: `error` (or `TEST_LOG_LEVEL` if set)

### Normal Mode
- **Interactive Logging**: Enabled
- **HTTP Request Logging**: Enabled
- **Error Logging**: Enabled
- **Log Level**: Uses `LOG_LEVEL` from config (default: `info`)

## Examples

### Running Tests with Minimal Logging
```bash
# Only errors will be logged
npm run start:test
```

### Running Tests with Full Logging for Debugging
```bash
# All logs including HTTP requests will be displayed
ENABLE_LOGGING=true TEST_LOG_LEVEL=debug npm run start:test
```

### Running Tests on Custom Port
```bash
# Run on port 8080 with no interactive logging
PORT=8080 npm run start:test
```

## Integration with Test Runners

The `createServer()` function can be used programmatically in test suites:

```javascript
import { createServer } from './index.js';

// Create server with no logging for tests
const server = createServer({
  enableInteractiveLogging: false,
  port: 4001,
  testMode: true
});

// Create server with logging for debugging tests
const debugServer = createServer({
  enableInteractiveLogging: true,
  port: 4002,
  testMode: true
});
```

This configuration ensures that test environments can run quietly by default, while still providing the flexibility to enable detailed logging when needed for debugging.
