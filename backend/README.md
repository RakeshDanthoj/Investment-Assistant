# FinnWise Backend

FastAPI service. Loads secrets from `../.env.local` at the repo root.

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
pytest -q
```
