#!/usr/bin/env python3
"""
Claude Code Hook Event Forwarder
Integrates with existing hook system to forward events to observability server
"""

import json
import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class HookEventHandler(FileSystemEventHandler):
    def __init__(self, project_root, server_url='http://localhost:4000/events'):
        self.project_root = Path(project_root)
        self.server_url = server_url
        self.hooks_dir = self.project_root / '.claude' / 'hooks'
        self.logs_dir = self.project_root / '.claude' / 'logs'
        
        # Ensure log directory exists
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Monitoring hooks directory: {self.hooks_dir}")
        print(f"📡 Forwarding events to: {self.server_url}")
    
    def on_created(self, event):
        if not event.is_directory:
            self.handle_event('created', event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.handle_event('modified', event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.handle_event('deleted', event.src_path)
    
    def handle_event(self, event_type, file_path):
        """Handle file system events in hooks directory"""
        file_path = Path(file_path)
        
        # Only process Python files in hooks directory
        if file_path.suffix == '.py' and str(file_path).startswith(str(self.hooks_dir)):
            self.forward_hook_event(event_type, file_path)
    
    def forward_hook_event(self, event_type, file_path):
        """Forward hook events to observability server"""
        try:
            # Create event data
            event_data = {
                'source_app': 'claude-dev-env',
                'session_id': 'dev-session',
                'hook_event_type': f'hook_{event_type}',
                'payload': {
                    'event_type': event_type,
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'timestamp': time.time()
                },
                'timestamp': int(time.time() * 1000)
            }
            
            # Use the existing send_event.py script to forward the event
            send_event_script = self.hooks_dir / 'send_event.py'
            if send_event_script.exists():
                self.call_send_event_script(event_data)
            else:
                print(f"⚠️  send_event.py not found at {send_event_script}")
            
        except Exception as e:
            print(f"❌ Error forwarding hook event: {e}")
    
    def call_send_event_script(self, event_data):
        """Call the existing send_event.py script to forward event"""
        try:
            send_event_script = self.hooks_dir / 'send_event.py'
            
            # Prepare command
            cmd = [
                'python3', str(send_event_script),
                '--source-app', 'claude-dev-env',
                '--event-type', event_data['hook_event_type'],
                '--server-url', self.server_url
            ]
            
            # Run the script with event data as input
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=json.dumps(event_data['payload']))
            
            if process.returncode == 0:
                print(f"✅ Event forwarded: {event_data['hook_event_type']}")
            else:
                print(f"⚠️  Event forwarding failed: {stderr}")
                
        except Exception as e:
            print(f"❌ Error calling send_event.py: {e}")

def monitor_hook_logs():
    """Monitor hook execution logs"""
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / '.claude' / 'logs'
    
    print(f"📊 Monitoring hook logs in: {logs_dir}")
    
    while True:
        try:
            # Check for new log files
            if logs_dir.exists():
                log_files = list(logs_dir.glob('*/*.json'))
                if log_files:
                    print(f"📋 Found {len(log_files)} log files")
                    
                    # Process recent log entries
                    for log_file in log_files:
                        try:
                            with open(log_file, 'r') as f:
                                log_data = json.load(f)
                                if isinstance(log_data, list) and log_data:
                                    latest_entry = log_data[-1]
                                    print(f"🔍 Latest log entry: {latest_entry.get('tool_name', 'unknown')}")
                        except Exception as e:
                            print(f"⚠️  Error reading log file {log_file}: {e}")
            
            time.sleep(10)
            
        except Exception as e:
            print(f"❌ Error monitoring logs: {e}")
            time.sleep(10)

def main():
    """Main entry point"""
    print("🚀 Starting Claude Code Hook Event Forwarder")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    server_url = os.getenv('HOOK_SERVER_URL', 'http://localhost:4000/events')
    
    # Create event handler
    event_handler = HookEventHandler(project_root, server_url)
    
    # Set up file system observer
    observer = Observer()
    observer.schedule(event_handler, str(event_handler.hooks_dir), recursive=True)
    
    # Start log monitor in separate thread
    log_monitor_thread = threading.Thread(target=monitor_hook_logs, daemon=True)
    log_monitor_thread.start()
    
    try:
        observer.start()
        print("👁️  File system observer started")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping hook event forwarder...")
        observer.stop()
        
    observer.join()
    print("✅ Hook event forwarder stopped")

if __name__ == "__main__":
    main()
