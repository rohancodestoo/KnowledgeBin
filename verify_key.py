import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    from notes import utils
    print(f"API Key present: {bool(utils.api_key)}")
    if utils.api_key:
        print(f"API Key (masked): {utils.api_key[:5]}...")
    
    print(f"Model initialized: {utils.model is not None}")
    
    if utils.model:
        try:
            print("Attempting test generation...")
            response = utils.model.generate_content("Hello, can you hear me?")
            print("Generation successful!")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Generation failed: {e}")
            
except Exception as e:
    print(f"Import failed: {e}")
