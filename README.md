# Travel Route Suggester API

An AI-powered travel route suggestion backend. Suggests routes based on historical travel patterns, real-time difficulty scoring, and user preferences.

## Features
- **LangGraph Agent Pipeline**: Orchestrates location resolution, route fetching, pattern retrieval, difficulty scoring, ranking, and explanation.
- **Difficulty Scoring**: Scores routes based on semantic trip history (stored in Qdrant) and real-time conditions.
- **Mock Mode**: Can run completely without API keys in Mock Mode.
- **FastAPI**: Modern, fast API backend.

## Setup

1. **Install dependencies**:
   This project uses `uv` or `pip`.
   ```bash
   pip install -r requirements.txt
   ```
   Or if you use a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Copy `.env.example` to `.env`.
   ```bash
   cp .env.example .env
   ```
   
   If you want to use the actual APIs, configure:
   - `GOOGLE_PLACES_API_KEY`
   - `ORS_API_KEY`
   - `LLM_API_KEY`
   
   If you don't have keys, simply set `MOCK_MODE=true` in your `.env`.

3. **Database**:
   By default, it uses SQLite (`sqlite+aiosqlite:///./dev.db`). No setup required.
   If using PostgreSQL, update `DATABASE_URL` in `.env`.

4. **Seed Data**:
   To seed the database with synthetic trip patterns:
   ```bash
   python scripts/seed_data.py
   ```

## Running the Server

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.
API documentation is available at `http://localhost:8000/docs`.

## Docker Compose

You can also run the entire stack (API, PostgreSQL, Qdrant) using Docker Compose:
```bash
docker-compose up -d
```

## Testing

Run the test suite with pytest:
```bash
pytest
```
To run tests with coverage:
```bash
pytest --cov=app tests/
```
