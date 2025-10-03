#!/usr/bin/env python3
"""
Test script to verify Ollama doesn't cache responses between requests
"""
import requests
import json
import time

def test_ollama_independence():
    """Test that Ollama gives different responses to the same simple query"""
    
    url = "http://localhost:11434/api/generate"
    
    # Test 1: Send "hey" twice with different timestamps
    print("=" * 60)
    print("TEST 1: Sending 'hey' twice with different seeds")
    print("=" * 60)
    
    for i in range(2):
        payload = {
            "model": "phi4-mini",
            "prompt": "CLIENT INQUIRY: hey\n\nRemember: This is a NEW conversation.",
            "stream": False,
            "system": "You are a legal counsel. This is a NEW conversation. Answer only the question asked.",
            "options": {
                "temperature": 0.7,
                "seed": int(time.time() * 1000000) % 2147483647
            }
        }
        
        print(f"\nRequest {i+1}:")
        print(f"  Seed: {payload['options']['seed']}")
        
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        print(f"  Response: {result['response'][:150]}...")
        print(f"  Context returned: {result.get('context', 'None')}")
        time.sleep(1)
    
    # Test 2: Test with explicit no-context by not providing context field
    print("\n" + "=" * 60)
    print("TEST 2: Checking if Ollama is using cached model state")
    print("=" * 60)
    
    # Clear any model state by making a simple request
    clear_payload = {
        "model": "phi4-mini",
        "prompt": "Say 'reset' and nothing else.",
        "stream": False,
        "options": {
            "seed": 12345
        }
    }
    
    print("\nSending clear request...")
    requests.post(url, json=clear_payload, timeout=30)
    time.sleep(1)
    
    # Now test our actual query
    test_payload = {
        "model": "phi4-mini",
        "prompt": "CLIENT INQUIRY: hey\n\nThis is a NEW conversation. Answer appropriately.",
        "stream": False,
        "system": "You are a legal counsel. This is a NEW CLIENT MEETING.",
        "options": {
            "temperature": 0.7,
            "seed": int(time.time() * 1000000) % 2147483647
        }
    }
    
    print("\nSending test request after clear...")
    response = requests.post(url, json=test_payload, timeout=30)
    result = response.json()
    print(f"Response: {result['response'][:200]}...")
    
    # Check if response mentions mergers or previous context
    response_text = result['response'].lower()
    if any(word in response_text for word in ['merger', 'x corp', 'y corporation', 'indemnification']):
        print("\n⚠️  WARNING: Response contains references to previous context!")
        print("This suggests Ollama might be caching or the model is hallucinating.")
    else:
        print("\n✅ Response looks clean - no previous context detected")

if __name__ == "__main__":
    test_ollama_independence()
