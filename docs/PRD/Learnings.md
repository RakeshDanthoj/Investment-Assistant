# Start the backend # 

cd c:\Projects\InvestmentAssistant\backend
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Start frontend #

npx pnpm@9 dev:frontend

or 

cd frontend
npm run dev

#Authentication disabled#

When you want auth again
Remove the env line (or set it to something other than true/1), keep NODE_ENV=production builds as today, and the previous behavior returns.