import requests

def test_pollinations():
    url = "https://text.pollinations.ai/"
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, are you there?"}
        ],
        "model": "openai"
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pollinations()
