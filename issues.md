# Pre-Deployment Review

Reviewed again on September 26, 2026 against the current local files,
`overview.md`, the public GitHub repository, and the configured Render service.
This is a review only; no application code was changed.

## Critical

### 1. The frontend is not currently published on GitHub Pages

The expected site URL and the likely `/frontend/` alternative both return 404:

- `https://martinhe123.github.io/aec_question_answering/`
- `https://martinhe123.github.io/aec_question_answering/frontend/`

GitHub's Pages endpoint for the repository also returns 404, which is consistent
with Pages not being configured. Visitors therefore cannot currently reach the
chat interface.

**Required before launch:** enable GitHub Pages for the repository and publish a
directory whose root contains `index.html`. The current frontend files are under
`frontend`, while GitHub Pages branch deployment normally publishes from the
repository root or `/docs`. Move or copy the static files to the chosen publish
root, or use a GitHub Actions Pages workflow that uploads `frontend`.

### 2. The public repository still points the frontend at localhost

The local working copy of `frontend/script.js` now correctly uses:

```javascript
const API_URL = "https://aec-question-answering.onrender.com/chat";
```

However, that change is uncommitted. The version currently on GitHub still uses
`http://127.0.0.1:8000/chat`. If Pages is enabled before the local change is
committed and pushed, each visitor's browser will try to contact the visitor's
own computer and the chat will fail. An HTTPS page may also block that HTTP
request as mixed content.

**Required before launch:** commit and push the API URL change, then confirm the
published `script.js` contains the Render HTTPS URL.

## Medium

### 3. The Render deployment configuration is not recorded as code

There is no `render.yaml`. The configured service is currently reachable and its
health route returns `200 {"status":"ok"}`, but rebuilding it still depends on
settings stored only in the Render dashboard. Because `main.py` and
`requirements.txt` are in `backend`, the expected settings are:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variable: `OPENAI_API_KEY` set to a valid project key

Record these settings in `render.yaml` or deployment documentation so the
service can be recreated without guesswork. Never commit the real API key.

### 4. A slow OpenAI request can leave the interface waiting for many minutes

The backend does not set an application-specific timeout or retry policy. With
the installed OpenAI client it inherits two retries and a 600-second read
timeout. The frontend `fetch` has no timeout or cancellation either, so the Send
button can remain disabled until the browser, Render, or upstream service ends
the request.

Set a shorter backend timeout and translate timeout failures into a friendly
error. Add an `AbortController` timeout in the browser so the interface recovers
at approximately the same time.

### 5. The public endpoint has only limited cost protection

`POST /chat` requires no authentication. Its ten-requests-per-minute limit is
stored only in one Python process, resets on every restart, and is not shared by
multiple instances. A caller can also bypass the frontend and call the endpoint
directly.

The OpenAI request sets no output-token limit, so a short input can still produce
a comparatively long paid response. Before sharing the site widely, use a
dedicated OpenAI project key, configure project budget alerts or limits, and set
a conservative response-token limit. Use a shared rate-limit store only if the
app grows beyond a small single-instance demo.

### 6. The rate limiter is not safe for concurrent updates

The synchronous `/chat` route can run in multiple worker threads, but
`request_log` is a shared `defaultdict` of mutable lists with no lock. Two
requests from the same address can prune, count, and append concurrently. This
can allow requests beyond the intended limit, and adding multiple server
processes would give each process a separate limit.

For a small demo, a lock around the in-memory check is sufficient. If the
service later runs multiple processes or instances, move rate limiting to a
shared service.

## Not So Urgent

### 7. The Python runtime version is not pinned

The local virtual environment uses Python 3.12, but the project does not declare
a Python version. A future hosting default change could alter dependency
behavior. Add a Render runtime setting or `.python-version` file when
reproducible deployments become important.

### 8. The local API-key fallback depends on the launch directory

`backend/main.py` opens `secrets.txt` using a relative path. It works when the
server is started inside `backend`, but not when it is imported or started from
the repository root unless `OPENAI_API_KEY` is already set. Resolve the file
relative to `main.py`, or document that local commands must run from `backend`.

### 9. `allow_credentials=True` is unnecessary for this frontend

The frontend does not send cookies or browser credentials. Keeping credentials
enabled with explicit origins is not currently a vulnerability, and the live
preflight correctly allows `https://martinhe123.github.io` while rejecting an
unlisted origin. Setting `allow_credentials=False` would describe the actual
request behavior more accurately.

### 10. Validation failures consume rate-limit slots

The limiter runs before empty-input and 200-word validation. Repeated malformed
requests therefore count toward the same limit as valid questions. This can be
reasonable for abuse protection, but it should be an intentional policy. If the
limit is meant to measure paid OpenAI calls, record the request only after
validation succeeds.

### 11. The local virtual environment is inside the project folder

`backend/.venv` contains generated dependency files. It is correctly excluded
by `.gitignore`, so it is not committed or deployed, but keeping it inside the
project adds storage and file-search noise. Moving it is optional.

### 12. The test client emits a dependency deprecation warning

Importing FastAPI's current `TestClient` emits a warning that the installed
Starlette test client's `httpx` integration is deprecated in favor of `httpx2`.
This does not affect the running service. Upgrade the related test dependencies
together rather than changing one package independently.

### 13. There is no repeatable automated test suite

Local checks passed for the health route, successful mocked chat response,
empty-input rejection, 200-word limit, and allowed and denied CORS preflights.
`frontend/script.js` also passes a JavaScript syntax check, and the installed
Python environment reports no broken requirements. These checks are not stored
as tests, so later changes can silently regress them. Add a small backend test
file and a basic frontend check once the app starts changing regularly.
