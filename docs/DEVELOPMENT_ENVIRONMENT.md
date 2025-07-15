# Claude Code Hooks Development Environment

This document describes the integrated development environment setup for Claude Code hooks with tmux-orchestrator, VS Code integration, and real-time observability.

## Overview

The development environment provides:
- **Tmux-orchestrator integration** for multi-pane development workflow
- **VS Code integration** with hooks output channel
- **Real-time hook monitoring** and forwarding to observability server
- **Multi-agent observability** with live event tracking

## Components

### 1. Python Launch Script (`scripts/launch_dev_env.py`)

The main launcher that:
- Creates and activates a Python virtual environment
- Installs required dependencies (tmux-orchestrator, watchdog, etc.)
- Generates tmux configuration
- Launches the complete development environment

#### Usage:
```bash
# Full setup and launch
python3 scripts/launch_dev_env.py

# Install dependencies only
python3 scripts/launch_dev_env.py --install-deps

# Create configuration files only
python3 scripts/launch_dev_env.py --config-only

# Launch without tmux (useful for debugging)
python3 scripts/launch_dev_env.py --no-tmux
```

### 2. Tmux Orchestrator Configuration (`config/orchestrator.yml`)

Defines a comprehensive tmux session with multiple windows:

#### Windows:
- **main**: VS Code and hooks watcher
- **servers**: Backend server (bun) and client dev server
- **hooks-monitor**: Node.js hooks proxy and system logs
- **hook-integration**: Python hook forwarder and VS Code bridge

#### Panes:
- **vs-code**: Launches VS Code in project directory
- **hooks-watch**: Monitors `.claude/hooks/` directory for changes
- **backend-server**: Runs `bun run dev` for backend API
- **client-dev**: Runs `bun run dev` for frontend client
- **hooks-cli**: Node.js proxy for VS Code integration
- **logs**: System logs and hook execution monitoring
- **hook-forwarder**: Python-based hook event forwarding
- **vscode-bridge**: VS Code output channel bridge

### 3. Node.js Hooks Proxy (`scripts/hooks-proxy.js`)

Provides real-time communication between hooks and VS Code:

#### Features:
- **HTTP Server**: Serves on port 8080 for VS Code extension
- **Server-Sent Events**: Real-time event streaming
- **File System Monitoring**: Watches hooks directory for changes
- **Tmux Integration**: Creates named pipes for tmux communication
- **CORS Support**: Enables cross-origin requests from VS Code

#### Endpoints:
- `GET /events`: Server-sent events stream for VS Code
- `GET /health`: Health check endpoint

### 4. Python Hook Event Forwarder (`scripts/hook-event-forwarder.py`)

Integrates with existing Claude Code hooks system:

#### Features:
- **File System Monitoring**: Uses watchdog to monitor hooks directory
- **Event Forwarding**: Integrates with existing `send_event.py` script
- **Log Monitoring**: Monitors hook execution logs
- **Observability Integration**: Forwards events to observability server

#### Integration:
- Calls existing `send_event.py` with proper arguments
- Monitors `.claude/hooks/` directory for Python file changes
- Forwards events to `http://localhost:4000/events` by default

### 5. VS Code Integration (`config/vscode-claude-hooks.json`)

Configuration for VS Code extension that connects to hooks proxy:

#### Features:
- **Auto-connection**: Automatically connects to hooks proxy on startup
- **Output Channel**: Creates "Claude Code" output channel
- **Commands**: Provides commands for connection management
- **Configuration**: Allows customization of proxy URL and settings

#### Commands:
- `claude-hooks.connect`: Connect to hooks proxy
- `claude-hooks.disconnect`: Disconnect from hooks proxy
- `claude-hooks.showOutput`: Show Claude hooks output channel

## Setup Instructions

### Prerequisites

1. **Python 3.8+** with pip
2. **Node.js 16+** with npm/bun
3. **tmux** installed
4. **VS Code** (optional, for IDE integration)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd claude-code-hooks-multi-agent-observability
   ```

2. **Install dependencies and launch**:
   ```bash
   python3 scripts/launch_dev_env.py
   ```

3. **Attach to tmux session**:
   ```bash
   tmux attach -t claude-dev-env
   ```

### Manual Setup (if orchestrator fails)

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python dependencies**:
   ```bash
   pip install tmux-orchestrator pyyaml requests python-dotenv watchdog
   ```

3. **Install Node.js dependencies**:
   ```bash
   npm install  # or bun install
   ```

4. **Start services manually**:
   ```bash
   # Terminal 1: Backend server
   cd apps/server && bun run dev
   
   # Terminal 2: Frontend client
   cd apps/client && bun run dev
   
   # Terminal 3: Hooks proxy
   node scripts/hooks-proxy.js
   
   # Terminal 4: Hook event forwarder
   python3 scripts/hook-event-forwarder.py
   ```

## Usage

### Starting the Development Environment

```bash
# Full startup
python3 scripts/launch_dev_env.py

# Attach to running session
tmux attach -t claude-dev-env

# List tmux sessions
tmux list-sessions
```

### Stopping the Development Environment

```bash
# Kill the tmux session
tmux kill-session -t claude-dev-env

# Or use existing script
./scripts/reset-system.sh
```

### Monitoring Hooks

1. **VS Code Output**: Open "Claude Code" output channel
2. **Tmux Logs**: Switch to logs pane in tmux
3. **Browser**: Visit `http://localhost:5173` for observability UI
4. **API**: Check `http://localhost:4000/events` for raw events

### Development Workflow

1. **Code Changes**: Edit files in VS Code (main tmux pane)
2. **Hook Monitoring**: Watch real-time hook events in logs pane
3. **Server Restart**: Servers auto-restart on file changes
4. **Observability**: View events in browser UI
5. **VS Code Integration**: See hook events in VS Code output channel

## Configuration

### Environment Variables

- `HOOK_SOURCE_APP`: Source application name (default: 'claude-dev-env')
- `HOOK_SERVER_URL`: Observability server URL (default: 'http://localhost:4000/events')

### Customization

- **Orchestrator Config**: Edit `config/orchestrator.yml`
- **Proxy Settings**: Modify `scripts/hooks-proxy.js`
- **VS Code Config**: Update `config/vscode-claude-hooks.json`

## Troubleshooting

### Common Issues

1. **Tmux not found**: Install tmux (`sudo apt install tmux` on Ubuntu)
2. **Python dependencies**: Ensure Python 3.8+ and pip are installed
3. **Node.js errors**: Check Node.js version (16+ required)
4. **Port conflicts**: Check if ports 4000, 5173, or 8080 are in use

### Debugging

1. **Check tmux session**:
   ```bash
   tmux list-sessions
   tmux attach -t claude-dev-env
   ```

2. **Check processes**:
   ```bash
   ps aux | grep -E "(bun|node|python)"
   ```

3. **Check logs**:
   ```bash
   tail -f /tmp/claude-hooks-proxy.log
   ```

4. **Test hooks proxy**:
   ```bash
   curl http://localhost:8080/health
   ```

## Advanced Features

### Custom Hook Integration

To integrate custom hooks:

1. Create hook script in `.claude/hooks/`
2. Ensure it follows the existing pattern
3. Events will be automatically forwarded to observability server

### VS Code Extension Development

To develop a full VS Code extension:

1. Use the configuration in `config/vscode-claude-hooks.json`
2. Implement the sample code provided
3. Connect to `http://localhost:8080/events` for real-time events

### Observability Server Integration

The system integrates with the existing observability server:

- Events are forwarded to `http://localhost:4000/events`
- Real-time visualization at `http://localhost:5173`
- WebSocket connection for live updates

## Files Overview

```
scripts/
├── launch_dev_env.py          # Main launcher script
├── hooks-proxy.js             # Node.js hooks proxy
└── hook-event-forwarder.py    # Python hook event forwarder

config/
├── orchestrator.yml           # Tmux orchestrator configuration
└── vscode-claude-hooks.json   # VS Code integration config

docs/
└── DEVELOPMENT_ENVIRONMENT.md # This documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test with the development environment
4. Submit a pull request

## License

This project is licensed under the MIT License.
