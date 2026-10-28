# GhanaSpeak TTS API

GhanaSpeak is a FastAPI backend for turning text and documents into speech in Ghanaian languages. It includes user authentication, document upload and web-article extraction, AI-assisted summaries and Q&A, podcast generation, and a user library for saved conversions.

## Features

- Register and authenticate users with bearer tokens.
- Upload PDF, DOCX, and plain-text documents, or extract an article from a URL.
- Translate text and synthesize speech through the Ghana NLP API.
- Generate summaries, answers, and two-host podcast scripts through Groq.
- Detect and protect scientific or sensitive words during text processing.
- Save generated audio locally and manage documents and conversion history.
- Provide admin endpoints for user management, statistics, and logs.

## Requirements

- Python 3.11
- PostgreSQL
- Git LFS, to download the included detection model
- API credentials for Ghana NLP and Groq for provider-backed features

## Setup

1. Clone the repository and download the model tracked with Git LFS:

   ```bash
   git lfs install
   git clone <repository-url>
   cd <repository-directory>
   git lfs pull
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install the application dependencies:

   ```bash
   python -m pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary pydantic-settings python-dotenv python-jose passlib[bcrypt] email-validator python-multipart requests beautifulsoup4 lxml groq transformers torch safetensors PyMuPDF python-docx pydub httpx
   ```

4. Create a `.env` file in the project root and set the required configuration:

   ```dotenv
   DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/ghanaspeak
   SECRET_KEY=replace-with-a-long-random-secret
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GHANA_NLP_API_KEY=your-ghana-nlp-api-key
   GROQ_API_KEY=your-groq-api-key
   AUDIO_STORAGE_PATH=static/audio
   SCIENTIFIC_WORDS_FILE=data/protects_list.json
   DEFAULT_MALE_VOICE=Kofi
   DEFAULT_FEMALE_VOICE=Akua
   ```

   Create the PostgreSQL database before running migrations. Keep real credentials in `.env`; do not commit them.

5. Apply database migrations:

   ```bash
   alembic upgrade head
   ```

6. Start the development server:

   ```bash
   uvicorn app.main:app --reload
   ```

The API is available at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs` and ReDoc at `http://127.0.0.1:8000/redoc`.

## API overview

| Area | Routes |
| --- | --- |
| Authentication | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Documents | `POST /upload`, `POST /scrape/`, `GET /documents`, `GET /documents/{document_id}`, `DELETE /documents/{document_id}` |
| Speech and AI | `POST /tts/`, `POST /summarise`, `POST /ask`, `POST /podcast` |
| Conversion library | `GET /library/`, `POST /library/`, `DELETE /library/{id}`, `POST /library/{id}/bookmark` |
| Administration | `GET /admin/users`, `PUT /admin/users/{id}`, `GET /admin/stats`, `GET /admin/logs` |

Most routes require an access token returned by registration or login:

```http
Authorization: Bearer <access_token>
```

See the interactive API docs for request and response schemas.

## Tests

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

The database regression tests require a disposable PostgreSQL database configured by `DATABASE_URL`. They create and remove a temporary schema, so do not point them at a production database. External provider calls are mocked by the tests.

## Model and generated files

The detection model weight file is managed by Git LFS. Run `git lfs pull` after cloning if the model file is missing or is only a small LFS pointer. Generated audio is written to `AUDIO_STORAGE_PATH` and is excluded from Git.
