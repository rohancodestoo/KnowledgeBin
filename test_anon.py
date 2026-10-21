import requests
import urllib.parse
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def test():
    # 1. Simple GET
    print("Test 1: Simple GET")
    try:
        r1 = requests.get('https://text.pollinations.ai/Hello', timeout=10)
        print(r1.text[:50])
    except Exception as e:
        print(f"Test 1 error: {e}")

    # 2. GET with system prompt
    print("\nTest 2: GET with system prompt")
    sys_prompt = "You are a creative AI."
    url2 = f"https://text.pollinations.ai/Hello?system={urllib.parse.quote(sys_prompt)}"
    try:
        r2 = requests.get(url2, timeout=10)
        print(r2.text[:100])
    except Exception as e:
        print(f"Test 2 error: {e}")

if __name__ == '__main__':
    test()
