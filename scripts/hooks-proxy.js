#!/usr/bin/env node
/**
 * Claude Code Hooks Proxy
 * Forwards hook events to VS Code output channel and tmux pipes
 */

import fs from 'fs';
import path from 'path';
import { spawn, exec } from 'child_process';
import http from 'http';
import url from 'url';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class HooksProxy {
    constructor() {
        this.projectRoot = path.resolve(__dirname, '..');
        this.logFile = '/tmp/claude-hooks-proxy.log';
        this.httpServer = null;
        this.clients = new Set();
        this.init();
    }

    init() {
        console.log('🔌 Starting Claude Code Hooks Proxy...');
        this.startHttpServer();
        this.monitorHooksDirectory();
        this.monitorHookEvents();
        this.setupSignalHandlers();
    }

    startHttpServer() {
        // Create HTTP server for VS Code extension communication
        this.httpServer = http.createServer((req, res) => {
            const parsedUrl = url.parse(req.url, true);
            
            // Enable CORS
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
            res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
            
            if (req.method === 'OPTIONS') {
                res.writeHead(200);
                res.end();
                return;
            }

            if (parsedUrl.pathname === '/events' && req.method === 'GET') {
                // Server-Sent Events endpoint
                res.writeHead(200, {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*'
                });
                
                // Add client to the set
                this.clients.add(res);
                
                // Send initial connection message
                res.write(`data: ${JSON.stringify({
                    type: 'connection',
                    message: 'Hooks proxy connected',
                    timestamp: new Date().toISOString()
                })}\\n\\n`);
                
                // Remove client when connection closes
                req.on('close', () => {
                    this.clients.delete(res);
                });
                
            } else if (parsedUrl.pathname === '/health' && req.method === 'GET') {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() }));
            } else {
                res.writeHead(404, { 'Content-Type': 'text/plain' });
                res.end('Not found');
            }
        });

        this.httpServer.listen(8081, () => {
            console.log('🌐 HTTP server started on port 8081');
            console.log('📡 VS Code extension can connect to http://localhost:8081/events');
        });
    }

    monitorHooksDirectory() {
        const hooksDir = path.join(this.projectRoot, '.claude', 'hooks');
        
        if (!fs.existsSync(hooksDir)) {
            console.log('⚠️  Hooks directory not found, creating...');
            fs.mkdirSync(hooksDir, { recursive: true });
        }

        // Watch for file changes in hooks directory
        try {
            fs.watch(hooksDir, { recursive: false }, (eventType, filename) => {
                if (filename && filename.endsWith('.py')) {
                    this.handleHookEvent('file_change', eventType, filename);
                }
            });
        } catch (error) {
            console.log('⚠️  File watching not available, using polling instead');
            // Fallback to polling if recursive watch is not available
            setInterval(() => {
                try {
                    const files = fs.readdirSync(hooksDir);
                    files.forEach(file => {
                        if (file.endsWith('.py')) {
                            this.handleHookEvent('file_check', 'polled', file);
                        }
                    });
                } catch (pollError) {
                    // Silently ignore polling errors
                }
            }, 2000);
        }

        console.log(`👁️  Monitoring hooks directory: ${hooksDir}`);
    }

    monitorHookEvents() {
        // Monitor for actual hook execution by watching log files and processes
        const logPatterns = [
            '/tmp/claude-hooks-*.log',
            '/tmp/claude-code-*.log',
            `${this.projectRoot}/.claude/logs/*.log`
        ];
        
        // Create a watcher for hook execution logs
        setInterval(() => {
            this.checkForHookExecutions();
        }, 1000);
    }

    checkForHookExecutions() {
        // Check for recent hook executions by monitoring system processes
        exec('ps aux | grep -E "(claude|hook)" | grep -v grep', (error, stdout, stderr) => {
            if (stdout) {
                const processes = stdout.split('\\n').filter(line => line.trim());
                processes.forEach(process => {
                    if (process.includes('claude') || process.includes('hook')) {
                        this.handleHookEvent('process_activity', 'running', process);
                    }
                });
            }
        });
    }

    handleHookEvent(source, eventType, data) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            type: 'hook_event',
            source: source,
            event: eventType,
            data: data,
            timestamp: timestamp,
            message: `[${source}] ${eventType}: ${typeof data === 'string' ? data : JSON.stringify(data)}`
        };

        // Log to file
        this.logToFile(logEntry);
        
        // Forward to VS Code via Server-Sent Events
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
        if (this.clients.size > 0) {
            const data = `data: ${JSON.stringify(entry)}\\n\\n`;
            this.clients.forEach(client => {
                try {
                    client.write(data);
                } catch (error) {
                    console.error('Error sending to VS Code client:', error);
                    this.clients.delete(client);
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
            if (this.httpServer) {
                this.httpServer.close();
            }
            process.exit(0);
        });
        
        process.on('SIGTERM', () => {
            console.log('\\n🛑 Received SIGTERM, shutting down...');
            if (this.httpServer) {
                this.httpServer.close();
            }
            process.exit(0);
        });
    }
}

// Start the proxy
console.log('🚀 Initializing Claude Code Hooks Proxy...');
new HooksProxy();
