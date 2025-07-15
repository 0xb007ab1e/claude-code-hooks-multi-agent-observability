#!/usr/bin/env python3
"""
Port Manager - Dynamic Port Assignment System
Manages port assignments starting from a base port number and tracks usage.
"""

import os
import json
from typing import Dict, List, Optional
from pathlib import Path
import threading

class PortManager:
    """Manages dynamic port assignment for services"""
    
    def __init__(self, base_port: int = None):
        self.base_port = base_port or int(os.getenv("BASE_PORT", "4000"))
        self.current_port = self.base_port
        self.assigned_ports = {}
        self.port_file = Path("./config/port_assignments.json")
        self.lock = threading.Lock()
        
        # Load existing assignments
        self._load_assignments()
        
    def _load_assignments(self):
        """Load port assignments from file"""
        try:
            if self.port_file.exists():
                with open(self.port_file, 'r') as f:
                    data = json.load(f)
                    self.assigned_ports = data.get("assignments", {})
                    self.current_port = data.get("next_port", self.base_port)
                    
                    # Validate that current_port is at least base_port
                    if self.current_port < self.base_port:
                        self.current_port = self.base_port
                        
        except (json.JSONDecodeError, FileNotFoundError):
            # Initialize with defaults
            self.assigned_ports = {}
            self.current_port = self.base_port
            
    def _save_assignments(self):
        """Save current port assignments to file"""
        data = {
            "base_port": self.base_port,
            "next_port": self.current_port,
            "assignments": self.assigned_ports
        }
        
        # Ensure config directory exists
        self.port_file.parent.mkdir(exist_ok=True)
        
        with open(self.port_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def assign_port(self, service_name: str, purpose: str = "") -> int:
        """
        Assign a port to a service
        
        Args:
            service_name: Name of the service requesting a port
            purpose: Description of what the port is used for
            
        Returns:
            int: Assigned port number
        """
        with self.lock:
            # Check if service already has a port assigned
            if service_name in self.assigned_ports:
                return self.assigned_ports[service_name]["port"]
            
            # Assign next available port
            assigned_port = self.current_port
            self.assigned_ports[service_name] = {
                "port": assigned_port,
                "purpose": purpose,
                "assigned_at": self._get_timestamp()
            }
            
            # Increment for next assignment
            self.current_port += 1
            
            # Save assignments
            self._save_assignments()
            
            return assigned_port
    
    def get_port(self, service_name: str) -> Optional[int]:
        """Get the assigned port for a service"""
        if service_name in self.assigned_ports:
            return self.assigned_ports[service_name]["port"]
        return None
    
    def get_next_port(self) -> int:
        """Get the next port that would be assigned"""
        return self.current_port
    
    def release_port(self, service_name: str) -> bool:
        """Release a port assignment"""
        with self.lock:
            if service_name in self.assigned_ports:
                del self.assigned_ports[service_name]
                self._save_assignments()
                return True
            return False
    
    def reset_assignments(self):
        """Reset all port assignments"""
        with self.lock:
            self.assigned_ports = {}
            self.current_port = self.base_port
            self._save_assignments()
    
    def list_assignments(self) -> Dict:
        """List all current port assignments"""
        return {
            "base_port": self.base_port,
            "next_port": self.current_port,
            "assignments": self.assigned_ports
        }
    
    def get_service_ports(self) -> Dict[str, int]:
        """Get a simple mapping of service names to ports"""
        return {
            service: info["port"] 
            for service, info in self.assigned_ports.items()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def export_env_vars(self) -> Dict[str, str]:
        """Export port assignments as environment variables"""
        env_vars = {
            "BASE_PORT": str(self.base_port),
            "NEXT_PORT": str(self.current_port)
        }
        
        # Add service-specific port variables
        for service, info in self.assigned_ports.items():
            # Convert service name to ENV var format
            env_var_name = f"{service.upper().replace('-', '_')}_PORT"
            env_vars[env_var_name] = str(info["port"])
            
        return env_vars
    
    def print_summary(self):
        """Print a summary of current port assignments"""
        print(f"\n{'='*60}")
        print("🚪 Port Assignment Summary")
        print(f"{'='*60}")
        print(f"📍 Base Port: {self.base_port}")
        print(f"🔢 Next Available Port: {self.current_port}")
        print(f"📊 Total Assigned Ports: {len(self.assigned_ports)}")
        print(f"{'='*60}")
        
        if self.assigned_ports:
            print("📋 Current Assignments:")
            for service, info in self.assigned_ports.items():
                print(f"  🔹 {service:<20} → Port {info['port']:<5} ({info['purpose']})")
        else:
            print("📋 No ports currently assigned")
        
        print(f"{'='*60}")


# Global port manager instance
port_manager = PortManager()

# Convenience functions for common operations
def assign_port(service_name: str, purpose: str = "") -> int:
    """Assign a port to a service"""
    return port_manager.assign_port(service_name, purpose)

def get_port(service_name: str) -> Optional[int]:
    """Get the assigned port for a service"""
    return port_manager.get_port(service_name)

def get_next_port() -> int:
    """Get the next port that would be assigned"""
    return port_manager.get_next_port()

def reset_ports():
    """Reset all port assignments"""
    port_manager.reset_assignments()

def list_ports() -> Dict:
    """List all current port assignments"""
    return port_manager.list_assignments()

def get_service_ports() -> Dict[str, int]:
    """Get a simple mapping of service names to ports"""
    return port_manager.get_service_ports()

def export_env_vars() -> Dict[str, str]:
    """Export port assignments as environment variables"""
    return port_manager.export_env_vars()
