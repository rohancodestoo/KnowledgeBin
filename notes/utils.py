import os
from pathlib import Path
import urllib.parse
import re
import requests
from dotenv import load_dotenv

# Load environment variables if not already loaded
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

api_key = os.environ.get('GOOGLE_API_KEY')

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
FALLBACK_GEMINI_MODEL = "gemini-3.8-flash"

class GeminiResponse:
    """Wrapper matching the Google Generative AI response structure."""
    def __init__(self, text: str):
        self.text = text

class GeminiModel:
    """Lightweight REST-based Gemini client using requests (no heavy SDK needed)."""
    def __init__(self, key: str, model_name: str = DEFAULT_GEMINI_MODEL):
        self.api_key = key
        self.model_name = model_name

    def generate_content(self, prompt: str, timeout: int = 10) -> GeminiResponse:
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not configured.")

        models_to_try = [self.model_name, FALLBACK_GEMINI_MODEL]
        last_error = None

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return GeminiResponse(parts[0].get("text", "").strip())
                elif resp.status_code in (404, 503):
                    # Try fallback model
                    continue
                else:
                    resp.raise_for_status()
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error
        raise RuntimeError("Failed to generate content from Gemini API.")

model = GeminiModel(api_key) if api_key else None


def generate_image_description(name: str) -> str:
    """Returns a description for a notebook cover based on its name."""
    if not name:
        return "A minimalist abstract notebook cover"
    return f"A minimalist abstract notebook cover for {name}"


def generate_image(description: str) -> str:
    """Generates an image URL using Pollinations.ai with graceful fallback."""
    try:
        encoded_prompt = urllib.parse.quote(str(description or "minimalist notebook cover"))
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}%20minimalist%20flat%20style%20vector%20art?width=256&height=256&nologo=true"
    except Exception as e:
        print(f"Error generating image: {e}")
        return "https://via.placeholder.com/256x256.png?text=No+Image"


def generate_completion(prompt: str) -> str:
    """Generates auto-completion for note content using Gemini, with safe fallback."""
    if model and prompt and prompt.strip():
        try:
            clean_prompt = prompt.strip()[-300:] # Focus on the immediate preceding context
            instruction = (
                f"Continue the following text naturally in 1 to 2 concise sentences. "
                f"Do NOT repeat the prompt. Return ONLY the continuation:\n\n{clean_prompt}"
            )
            res = model.generate_content(instruction, timeout=8)
            if res.text:
                return res.text
        except Exception as e:
            print(f"Gemini completion error: {e}")

    return " [AI Completion Disabled]"


def generate_summary(content: str) -> str:
    """Generates a summary of note content using Gemini, with safe fallback."""
    if model and content and content.strip():
        try:
            instruction = (
                f"Summarize the following note content in 2 to 3 concise, clear sentences. "
                f"Return only the summary text:\n\n{content.strip()}"
            )
            res = model.generate_content(instruction, timeout=10)
            if res.text:
                return res.text
        except Exception as e:
            print(f"Gemini summary error: {e}")

    return "AI Summary generation is currently disabled."


def generate_tags(content: str) -> list[str]:
    """Suggests relevant tags for note content using Gemini, with safe fallback."""
    if model and content and content.strip():
        try:
            instruction = (
                f"Suggest 3 to 5 relevant lowercase single-word tags for the following note content. "
                f"Return ONLY a comma-separated list of tags, without bullet points, numbers, or markdown (e.g. note, ideas, project):\n\n{content.strip()}"
            )
            res = model.generate_content(instruction, timeout=10)
            if res.text:
                # Parse comma-separated tags
                raw_tags = res.text.replace('\n', ',').split(',')
                tags = []
                for t in raw_tags:
                    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', t.strip().lower())
                    if cleaned and len(cleaned) <= 50 and cleaned not in tags:
                        tags.append(cleaned)
                if tags:
                    return tags[:5]
        except Exception as e:
            print(f"Gemini tag generation error: {e}")

    return ["note"]