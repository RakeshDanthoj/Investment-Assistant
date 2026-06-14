# Start the python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
backend # 

cd c:\Projects\InvestmentAssistant\backend

# Start frontend #

npx pnpm@9 dev:frontend

or 

cd frontend
npm run dev

#Authentication disabled#

When you want auth again
Remove the env line (or set it to something other than true/1), keep NODE_ENV=production builds as today, and the previous behavior returns.

#Pushing the migrations to DB#

pip install -e "./backend[dev]"  
python scripts/apply_migrations.py
#To check if the migrations are applied successfully, run the below in Supabase #

SELECT filename, applied_at
FROM public.schema_migrations
ORDER BY applied_at;


Monitoring Job:

cd backend
python -m app.jobs.signal_monitor


Interview points:

“Led performance remediation for two core product surfaces: cut time-to-content from ~9s to ~2.5s and raised mobile quality scores from ~80 to 96 by fixing backend data access, server-first rendering, and targeted frontend loading — with automated regression checks.”

If you want, I can turn this into a STAR-format answer (Situation / Task / Action / Result) for a specific role (e.g. full-stack vs platform).


GEMINI_API_KEY=AIzaSyAA3IU6BSnfsKCl_7y58ga9Ken-xIwhfzI


NVDIA API Key: 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

import requests, base64

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = False

def read_b64(path):
  with open(path, "rb") as f:
    return base64.b64encode(f.read()).decode()

headers = {
  "Authorization": "Bearer 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",
  "Accept": "text/event-stream" if stream else "application/json"
}

payload = {
  "model": "moonshotai/kimi-k2.6",
  "messages": [{"role":"user","content":""}],
  "max_tokens": 16384,
  "temperature": 1.00,
  "top_p": 1.00,
  "stream": stream,
  
}

response = requests.post(invoke_url, headers=headers, json=payload, stream=stream)
if stream:
    for line in response.iter_lines():
        if line:
            print(line.decode("utf-8"))
else:
    print(response.json())