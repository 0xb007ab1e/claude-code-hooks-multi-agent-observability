#!/usr/bin/env python3
"""
Simple test script to verify FastAPI app functionality
"""
import sys
import os
import asyncio
import httpx
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import create_app

@pytest.mark.asyncio
async def test_app():
    """Test the FastAPI app endpoints"""
    app = create_app(test_mode=True)
    
    # Use httpx AsyncClient with transport
    transport = httpx.ASGITransport(app=app)
    
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("Testing FastAPI app endpoints:")
        
        # Test root endpoint
        response = await client.get("/")
        print(f"GET / - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test health endpoint
        response = await client.get("/health")
        print(f"GET /health - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test events count endpoint
        response = await client.get("/events/count")
        print(f"GET /events/count - Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_app())
