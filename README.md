KnowledgeBin — AI-Powered Notes & Knowledge Workspace
------------------------------------------------------

Setup:
1. Create a virtualenv and install requirements:
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt

2. Configure environment variables in `.env`:
   GOOGLE_API_KEY=your_gemini_api_key
   DEBUG=True

3. Run migrations and create a superuser:
   python manage.py migrate
   python manage.py createsuperuser

4. Run the dev server:
   python manage.py runserver

Testing:
- Run all automated tests:
  python manage.py test

- Run utility tests:
  python test_utils_full.py
  python verify_key.py

Features:
- Note creation with optional AI cover generation (Pollinations.ai) or image upload
- Dynamic TipTap rich-text editor with markdown formatting, task lists, and code blocks
- Live auto-save with status indicator
- Gemini-powered AI autocomplete, summarization, and automated tagging
- Theme switching: Light, Dark, Midnight, and Sepia
- Note management: Pin, Archive, Trash (soft-delete), and Permanent Deletion
- Export to PDF and TXT
