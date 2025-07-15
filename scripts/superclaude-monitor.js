#!/usr/bin/env node

/**
 * SuperClaude Integration Monitor
 * 
 * Monitors SuperClaude framework usage and sends events to the observability system.
 * Since SuperClaude v3 removed hooks, this script monitors for indirect indicators
 * of SuperClaude usage and integrates with the multi-agent observability system.
 */

import fs from 'fs';
import path from 'path';
import http from 'http';
import { exec } from 'child_process';

// Configuration
const SUPERCLAUDE_PATH = '/home/b007ab1e/.claude';
const OBSERVABILITY_HOST = 'localhost';
const OBSERVABILITY_PORT = 4000;
const MONITOR_INTERVAL = 5000; // 5 seconds

// SuperClaude metadata file
const METADATA_FILE = path.join(SUPERCLAUDE_PATH, '.superclaude-metadata.json');

// Track previous state
let previousState = {
    metadataModified: null,
    commandsUsed: new Set(),
    lastActivity: null
};

/**
 * Send event to observability system
 */
function sendEvent(eventData) {
    const postData = JSON.stringify({
        source_app: 'superclaude-monitor',
        session_id: `superclaude-${Date.now()}`,
        hook_event_type: 'SuperClaudeActivity',
        payload: eventData,
        timestamp: new Date().toISOString()
    });

    const options = {
        hostname: OBSERVABILITY_HOST,
        port: OBSERVABILITY_PORT,
        path: '/events',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData)
        }
    };

    const req = http.request(options, (res) => {
        if (res.statusCode === 200) {
            console.log(`✅ Event sent: ${eventData.activity_type}`);
        } else {
            console.log(`❌ Failed to send event: ${res.statusCode}`);
        }
    });

    req.on('error', (err) => {
        console.log(`🔴 Error sending event: ${err.message}`);
    });

    req.write(postData);
    req.end();
}

/**
 * Check SuperClaude metadata for changes
 */
function checkMetadataChanges() {
    try {
        if (!fs.existsSync(METADATA_FILE)) {
            return null;
        }

        const stats = fs.statSync(METADATA_FILE);
        const currentModified = stats.mtime.getTime();

        if (previousState.metadataModified === null) {
            previousState.metadataModified = currentModified;
            return null;
        }

        if (currentModified > previousState.metadataModified) {
            previousState.metadataModified = currentModified;
            
            const metadata = JSON.parse(fs.readFileSync(METADATA_FILE, 'utf8'));
            
            sendEvent({
                activity_type: 'metadata_change',
                framework_version: metadata.superclaude?.version || 'unknown',
                components: Object.keys(metadata.components || {}),
                installation_type: metadata.framework?.installation_type || 'unknown',
                enabled: metadata.superclaude?.enabled || false,
                profile: metadata.superclaude?.profile || 'default'
            });
        }
    } catch (error) {
        console.log(`⚠️  Error checking metadata: ${error.message}`);
    }
}

/**
 * Monitor Claude Code processes for SuperClaude usage
 */
function monitorClaudeProcesses() {
    exec('ps aux | grep -i claude | grep -v grep', (error, stdout, stderr) => {
        if (error) {
            return;
        }

        const processes = stdout.split('\n').filter(line => line.trim());
        const claudeProcesses = processes.filter(line => 
            line.includes('claude') && !line.includes('grep')
        );

        if (claudeProcesses.length > 0) {
            sendEvent({
                activity_type: 'claude_process_detected',
                process_count: claudeProcesses.length,
                framework_status: 'active',
                timestamp: new Date().toISOString()
            });
        }
    });
}

/**
 * Check for SuperClaude framework files
 */
function checkFrameworkFiles() {
    try {
        const frameworkFiles = [
            'CLAUDE.md',
            'COMMANDS.md',
            'PERSONAS.md',
            'ORCHESTRATOR.md',
            'MCP.md'
        ];

        const existingFiles = frameworkFiles.filter(file => 
            fs.existsSync(path.join(SUPERCLAUDE_PATH, file))
        );

        if (existingFiles.length > 0) {
            sendEvent({
                activity_type: 'framework_status',
                framework_files: existingFiles.length,
                total_expected: frameworkFiles.length,
                installation_complete: existingFiles.length === frameworkFiles.length,
                available_files: existingFiles
            });
        }
    } catch (error) {
        console.log(`⚠️  Error checking framework files: ${error.message}`);
    }
}

/**
 * Monitor SuperClaude command directory
 */
function monitorCommandDirectory() {
    try {
        const commandsPath = path.join(SUPERCLAUDE_PATH, 'commands');
        
        if (!fs.existsSync(commandsPath)) {
            return;
        }

        const commandFiles = fs.readdirSync(commandsPath).filter(file => 
            file.endsWith('.md')
        );

        if (commandFiles.length > 0) {
            sendEvent({
                activity_type: 'commands_available',
                command_count: commandFiles.length,
                available_commands: commandFiles.map(f => f.replace('.md', '')),
                commands_path: commandsPath
            });
        }
    } catch (error) {
        console.log(`⚠️  Error monitoring command directory: ${error.message}`);
    }
}

/**
 * Start monitoring
 */
function startMonitoring() {
    console.log('🚀 SuperClaude Monitor started');
    console.log(`📁 Monitoring path: ${SUPERCLAUDE_PATH}`);
    console.log(`🔗 Observability endpoint: http://${OBSERVABILITY_HOST}:${OBSERVABILITY_PORT}/events`);
    console.log(`⏰ Monitor interval: ${MONITOR_INTERVAL}ms`);

    // Send initial status
    sendEvent({
        activity_type: 'monitor_started',
        superclaude_path: SUPERCLAUDE_PATH,
        monitor_version: '1.0.0',
        capabilities: ['metadata_monitoring', 'process_detection', 'framework_status']
    });

    // Set up monitoring intervals
    setInterval(checkMetadataChanges, MONITOR_INTERVAL);
    setInterval(monitorClaudeProcesses, MONITOR_INTERVAL * 2); // Every 10 seconds
    setInterval(checkFrameworkFiles, MONITOR_INTERVAL * 4); // Every 20 seconds  
    setInterval(monitorCommandDirectory, MONITOR_INTERVAL * 6); // Every 30 seconds
}

/**
 * Handle graceful shutdown
 */
process.on('SIGTERM', () => {
    console.log('📴 SuperClaude Monitor shutting down...');
    sendEvent({
        activity_type: 'monitor_stopped',
        reason: 'SIGTERM',
        uptime: process.uptime()
    });
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('📴 SuperClaude Monitor shutting down...');
    sendEvent({
        activity_type: 'monitor_stopped',
        reason: 'SIGINT',
        uptime: process.uptime()
    });
    process.exit(0);
});

// Start monitoring
startMonitoring();
