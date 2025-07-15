#!/usr/bin/env python3
import sys
import os
import subprocess

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Run the server
if __name__ == "__main__":
    # Change to the server directory
    os.chdir(os.path.dirname(__file__))
    
    # Run the server
    cmd = [sys.executable, "src/main.py"] + sys.argv[1:]
    subprocess.run(cmd)
