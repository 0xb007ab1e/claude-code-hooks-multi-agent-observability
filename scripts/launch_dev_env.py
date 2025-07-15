#!/usr/bin/env python3
"""
Development Environment Launcher with Tmux-Orchestrator Integration
Launches a comprehensive development environment with VS Code, watch processes, and backend servers.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# Try importing yaml, install if needed
try:
    import yaml
except ImportError:
    print("🔧 Installing required dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml"], check=True)
    import yaml

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.absolute()

def activate_venv():
    """Activate virtual environment or create one if it doesn't exist."""
    project_root = get_project_root()
    venv_path = project_root / "venv"
    
    if not venv_path.exists():
        print("🔧 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("✅ Virtual environment created")
    
    # Activate venv based on OS
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        activate_script = venv_path / "bin" / "activate"
        python_exe = venv_path / "bin" / "python"
    
    print(f"📦 Using virtual environment: {venv_path}")
    return str(python_exe), str(activate_script)

def install_dependencies():
    """Install required dependencies."""
    project_root = get_project_root()
    python_exe, _ = activate_venv()
    
    # Install tmux-orchestrator if not available
    try:
        result = subprocess.run([python_exe, "-m", "pip", "show", "tmux-orchestrator"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("🔧 Installing tmux-orchestrator...")
            subprocess.run([python_exe, "-m", "pip", "install", "tmux-orchestrator"], check=True)
            print("✅ tmux-orchestrator installed")
    except subprocess.CalledProcessError:
        print("⚠️  Warning: Could not install tmux-orchestrator. Please install manually.")
    
    # Install other dependencies
    dependencies = [
        "pyyaml",
        "requests",
        "python-dotenv",
        "watchdog"
    ]
    
    for dep in dependencies:
        try:
            result = subprocess.run([python_exe, "-m", "pip", "show", dep], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"🔧 Installing {dep}...")
                subprocess.run([python_exe, "-m", "pip", "install", dep], check=True)
                print(f"✅ {dep} installed")
        except subprocess.CalledProcessError:
            print(f"⚠️  Warning: Could not install {dep}")

def check_tmux():
    """Check if tmux is available."""
    try:
        subprocess.run(["tmux", "-V"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def ensure_config_dir():
    """Ensure config directory exists."""
    project_root = get_project_root()
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir

def create_orchestrator_config():
    """Create or update the orchestrator.yml configuration."""
    config_dir = ensure_config_dir()
    orchestrator_config = config_dir / "orchestrator.yml"
    project_root = get_project_root()
    
    # Create the configuration
    config = {
        "session_name": "claude-dev-env",
        "project_root": str(project_root),
        "windows": [
            {
                "name": "main",
                "layout": "main-horizontal",
                "panes": [
                    {
                        "name": "vs-code",
                        "commands": [
                            f"cd {project_root}",
                            "code .",
                            "echo '🚀 VS Code launched for Claude Code Hooks project'"
                        ]
                    },
                    {
                        "name": "hooks-watch",
                        "commands": [
                            f"cd {project_root}",
                            "# Watch for changes in hooks and restart processes",
                            "echo '👁️  Watching hooks directory for changes...'",
                            "while true; do",
                            "  echo '$(date): Hooks watcher active - monitoring .claude/hooks/'",
                            "  sleep 10",
                            "done"
                        ]
                    }
                ]
            },
            {
                "name": "servers",
                "layout": "even-horizontal",
                "panes": [
                    {
                        "name": "backend-server",
                        "commands": [
                            f"cd {project_root}/apps/server",
                            "echo '🖥️  Starting backend server...'",
                            "BUN=${BUN:-$(command -v bun || echo ~/.bun/bin/bun)}",
                            "$BUN run dev"
                        ]
                    },
                    {
                        "name": "client-dev",
                        "commands": [
                            f"cd {project_root}/apps/client",
                            "echo '🎨 Starting client development server...'",
                            "BUN=${BUN:-$(command -v bun || echo ~/.bun/bin/bun)}",
                            "$BUN run dev"
                        ]
                    }
                ]
            },
            {
                "name": "hooks-monitor",
                "layout": "even-vertical",
                "panes": [
                    {
                        "name": "hooks-cli",
                        "commands": [
                            f"cd {project_root}",
                            "echo '🔌 Claude Code Hooks CLI Monitor'",
                            "echo '📊 This pane monitors hook events and forwards to observability system'",
                            "echo '🚀 Starting hooks proxy with VS Code integration on port 8081...'",
                            "node scripts/hooks-proxy.js"
                        ]
                    },
                    {
                        "name": "logs",
                        "commands": [
                            f"cd {project_root}",
                            "echo '📋 System Logs and Output'",
                            "echo '⚡ Real-time monitoring of Claude agent activity'",
                            "tail -f /tmp/claude-hooks-*.log 2>/dev/null || echo 'No active log files yet'"
                        ]
                    }
                ]
            }
        ]
    }
    
    with open(orchestrator_config, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)
    
    print(f"✅ Orchestrator configuration created: {orchestrator_config}")
    return orchestrator_config

def create_hooks_proxy():
    """Create Node.js proxy script for hooks output forwarding."""
    project_root = get_project_root()
    proxy_script = project_root / "scripts" / "hooks-proxy.js"
    
    proxy_content = '''#!/usr/bin/env node
/**
 * Claude Code Hooks Proxy
 * Forwards hook events to VS Code output channel and tmux pipes
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const WebSocket = require('ws');

class HooksProxy {
    constructor() {
        this.projectRoot = path.resolve(__dirname, '..');
        this.logFile = '/tmp/claude-hooks-proxy.log';
        this.wsServer = null;
        this.init();
    }

    init() {
        console.log('🔌 Starting Claude Code Hooks Proxy...');
        this.startWebSocketServer();
        this.monitorHooksDirectory();
        this.setupSignalHandlers();
    }

    startWebSocketServer() {
        // Create WebSocket server for VS Code extension communication
        this.wsServer = new WebSocket.Server({ port: 8080 });
        
        this.wsServer.on('connection', (ws) => {
            console.log('📡 VS Code extension connected');
            ws.send(JSON.stringify({
                type: 'connection',
                message: 'Hooks proxy connected',
                timestamp: new Date().toISOString()
            }));
        });

        console.log('🌐 WebSocket server started on port 8080');
    }

    monitorHooksDirectory() {
        const hooksDir = path.join(this.projectRoot, '.claude', 'hooks');
        
        if (!fs.existsSync(hooksDir)) {
            console.log('⚠️  Hooks directory not found, creating...');
            fs.mkdirSync(hooksDir, { recursive: true });
        }

        // Watch for file changes in hooks directory
        fs.watch(hooksDir, { recursive: true }, (eventType, filename) => {
            if (filename && filename.endsWith('.py')) {
                this.handleHookEvent(eventType, filename);
            }
        });

        console.log(`👁️  Monitoring hooks directory: ${hooksDir}`);
    }

    handleHookEvent(eventType, filename) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            type: 'hook_event',
            event: eventType,
            file: filename,
            timestamp: timestamp,
            message: `Hook ${eventType}: ${filename}`
        };

        // Log to file
        this.logToFile(logEntry);
        
        // Forward to VS Code via WebSocket
        this.forwardToVSCode(logEntry);
        
        // Send to tmux pipe if available
        this.sendToTmuxPipe(logEntry);
        
        console.log(`📝 ${timestamp} - ${logEntry.message}`);
    }

    logToFile(entry) {
        const logLine = `${entry.timestamp} [${entry.type}] ${entry.message}\\n`;
        fs.appendFile(this.logFile, logLine, (err) => {
            if (err) console.error('Error writing to log file:', err);
        });
    }

    forwardToVSCode(entry) {
        if (this.wsServer) {
            this.wsServer.clients.forEach((client) => {
                if (client.readyState === WebSocket.OPEN) {
                    client.send(JSON.stringify(entry));
                }
            });
        }
    }

    sendToTmuxPipe(entry) {
        // Create a named pipe for tmux communication
        const pipePath = '/tmp/claude-hooks-pipe';
        
        try {
            if (!fs.existsSync(pipePath)) {
                spawn('mkfifo', [pipePath]);
            }
            
            const pipeMessage = `${entry.timestamp} [Claude Hooks] ${entry.message}\\n`;
            fs.writeFile(pipePath, pipeMessage, { flag: 'a' }, (err) => {
                if (err && err.code !== 'EPIPE') {
                    console.error('Error writing to tmux pipe:', err);
                }
            });
        } catch (error) {
            // Silently fail if pipe operations don't work
        }
    }

    setupSignalHandlers() {
        process.on('SIGINT', () => {
            console.log('\\n🛑 Shutting down hooks proxy...');
            if (this.wsServer) {
                this.wsServer.close();
            }
            process.exit(0);
        });
    }
}

// Start the proxy
new HooksProxy();
'''
    
    with open(proxy_script, 'w') as f:
        f.write(proxy_content)
    
    # Make executable
    os.chmod(proxy_script, 0o755)
    print(f"✅ Hooks proxy script created: {proxy_script}")
    return proxy_script

def launch_tmux_session():
    """Launch the tmux session using orchestrator."""
    project_root = get_project_root()
    config_path = project_root / "config" / "orchestrator.yml"
    python_exe, _ = activate_venv()
    
    if not check_tmux():
        print("❌ tmux is not available. Please install tmux first.")
        return False
    
    try:
        # Kill existing session if it exists
        subprocess.run(["tmux", "kill-session", "-t", "claude-dev-env"], 
                      capture_output=True)
        
        # Launch new session with orchestrator
        print("🚀 Launching tmux session with orchestrator...")
        
        # Use tmux-orchestrator if available, otherwise create session manually
        try:
            result = subprocess.run([python_exe, "-m", "tmux_orchestrator", str(config_path)], 
                                  check=True, capture_output=True, text=True)
            print("✅ Tmux session launched successfully")
            return True
        except subprocess.CalledProcessError:
            print("⚠️  tmux-orchestrator not working, creating session manually...")
            return create_tmux_session_manually()
            
    except Exception as e:
        print(f"❌ Error launching tmux session: {e}")
        return False

def create_tmux_session_manually():
    """Create tmux session manually if orchestrator fails."""
    project_root = get_project_root()
    
    try:
        # Create new session
        subprocess.run(["tmux", "new-session", "-d", "-s", "claude-dev-env"], check=True)
        
        # Create windows and panes
        subprocess.run(["tmux", "rename-window", "-t", "claude-dev-env:0", "main"], check=True)
        
        # Split into panes
        subprocess.run(["tmux", "split-window", "-h", "-t", "claude-dev-env:main"], check=True)
        subprocess.run(["tmux", "split-window", "-v", "-t", "claude-dev-env:main.1"], check=True)
        
        # Send commands to panes
        subprocess.run(["tmux", "send-keys", "-t", "claude-dev-env:main.0", 
                       f"cd {project_root} && code .", "Enter"], check=True)
        
        subprocess.run(["tmux", "send-keys", "-t", "claude-dev-env:main.1", 
                       f"cd {project_root}/apps/server && BUN=${{BUN:-$(command -v bun || echo ~/.bun/bin/bun)}} && $BUN run dev", "Enter"], check=True)
        
        subprocess.run(["tmux", "send-keys", "-t", "claude-dev-env:main.2", 
                       f"cd {project_root}/apps/client && BUN=${{BUN:-$(command -v bun || echo ~/.bun/bin/bun)}} && $BUN run dev", "Enter"], check=True)
        
        # Create additional window for hooks
        subprocess.run(["tmux", "new-window", "-t", "claude-dev-env", "-n", "hooks"], check=True)
        subprocess.run(["tmux", "send-keys", "-t", "claude-dev-env:hooks", 
                       f"cd {project_root} && node scripts/hooks-proxy.js", "Enter"], check=True)
        
        print("✅ Tmux session created manually")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating tmux session manually: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Launch Claude Code development environment')
    parser.add_argument('--no-tmux', action='store_true', help='Skip tmux session creation')
    parser.add_argument('--config-only', action='store_true', help='Only create configuration files')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies and exit')
    
    args = parser.parse_args()
    
    print("🎯 Claude Code Hooks Development Environment Launcher")
    print("=" * 55)
    
    try:
        # Install dependencies
        if args.install_deps or not args.config_only:
            install_dependencies()
        
        # Create configuration files
        create_orchestrator_config()
        # create_hooks_proxy()  # Already exists, skip recreation
        
        if args.config_only:
            print("✅ Configuration files created successfully")
            return
        
        if args.install_deps:
            print("✅ Dependencies installed successfully")
            return
        
        # Launch tmux session
        if not args.no_tmux:
            success = launch_tmux_session()
            if success:
                print("🎉 Development environment launched successfully!")
                print("💡 Use 'tmux attach -t claude-dev-env' to attach to the session")
                print("💡 Use 'tmux kill-session -t claude-dev-env' to stop the session")
            else:
                print("❌ Failed to launch tmux session")
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\\n🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
