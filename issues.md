# Deployment Review

Reviewed again on September 26, 2026 against the current local files, the
public GitHub repository, the successful GitHub Pages workflow, and the live
GitHub Pages and Render deployments. This is a review only; no application code
was changed.

## Critical

No current critical issues were found.

The previous launch blockers are resolved:

- `https://martinhe123.github.io/aec_question_answering/` returns the frontend
  successfully.
- The deployed `script.js` uses the Render HTTPS `/chat` endpoint.
- The latest GitHub Pages workflow completed successfully.
- The Render health route returns `200 {"status":"ok"}`.
- The live CORS preflight allows `https://martinhe123.github.io`.

## Medium

### 1. A slow OpenAI request can leave the interface waiting for many minutes

The backend does not set an application-specific timeout or retry policy. With
the installed OpenAI client it inherits two retries and a 600-second read
timeout. The frontend `fetch` has no timeout or cancellation either, so the Send
button can remain disabled until the browser, Render, or upstream service ends
the request.

Set a shorter backend timeout and translate timeout failures into a friendly
error. Add an `AbortController` timeout in the browser so the interface recovers
at approximately the same time.

### 2. The public endpoint has only limited cost protection

`POST /chat` requires no authentication. Its ten-requests-per-minute limit is
stored only in one Python process, resets on every restart, and is not shared by
multiple instances. A caller can bypass the frontend and call the endpoint
directly.

The OpenAI request sets no output-token limit, so a short input can still produce
a comparatively long paid response. For wider sharing, use a dedicated OpenAI
project key, configure project budget alerts or limits, and set a conservative
response-token limit. A shared rate-limit store is only necessary if this grows
beyond a small single-instance demonstration.

### 3. The Render deployment configuration is not recorded as code

There is no `render.yaml`. The live service is healthy, but rebuilding it still
depends on settings stored only in the Render dashboard. The expected settings
are:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variable: `OPENAI_API_KEY` set to a valid project key

Record these settings in `render.yaml` or deployment documentation so the
service can be recreated without guesswork. Never commit the real API key.

## Not So Urgent

### 4. The rate limiter has single-process and concurrency limitations

The synchronous `/chat` route can run in multiple worker threads, but
`request_log` is a shared mutable dictionary of lists with no lock. Concurrent
requests from the same address can pass the check at the same time. Multiple
server processes or instances would also maintain separate limits.

For this small single-instance app, a lock around the in-memory check would
improve consistency. If the service later scales, move rate limiting to a shared
service.

### 5. Validation failures consume rate-limit slots

The limiter runs before empty-input and 200-word validation. Repeated malformed
requests therefore count toward the same limit as valid questions. This can be
reasonable for abuse protection, but it should be intentional. If the limit is
meant to measure paid OpenAI calls, record the request only after validation
succeeds.

### 6. The Python runtime version is not pinned

The local virtual environment uses Python 3.12, but the project does not declare
a Python version. A future hosting default change could alter dependency
behavior. Add a Render runtime setting or `.python-version` file when
reproducible deployments become important.

### 7. The local API-key fallback depends on the launch directory

`backend/main.py` opens `secrets.txt` using a relative path. It works when the
server is started inside `backend`, but not when it is imported or started from
the repository root unless `OPENAI_API_KEY` is already set. Resolve the file
relative to `main.py`, or document that local commands must run from `backend`.

### 8. `allow_credentials=True` is unnecessary for this frontend

The frontend does not send cookies or browser credentials. Keeping credentials
enabled with explicit origins is not currently a vulnerability, and the live
preflight behaves correctly. Setting `allow_credentials=False` would describe
the application's actual request behavior more accurately.

### 9. An unexpected empty model response becomes an internal server error

The OpenAI SDK types message content as optional, but the response model requires
a string. If the API ever returns a choice without text content,
`ChatResponse(response=answer)` will raise a validation error and the visitor
will receive a generic server failure. Check that the response contains text and
return a controlled 502 error when it does not.

### 10. The local virtual environment is inside the project folder

`backend/.venv` contains generated dependency files. It is correctly excluded
by `.gitignore`, so it is not committed or deployed, but keeping it inside the
project adds storage and file-search noise. Moving it is optional.

### 11. The test client emits a dependency deprecation warning

Importing FastAPI's current `TestClient` emits a warning that the installed
Starlette test client's `httpx` integration is deprecated in favor of `httpx2`.
This does not affect the deployed service. Upgrade the related test dependencies
together rather than changing one package independently.

### 12. There is no repeatable automated test suite

Local checks passed for the health route, successful mocked chat response,
empty-input rejection, and 200-word limit. The deployed site, JavaScript API
URL, workflow result, backend health, and production CORS were also checked.
`frontend/script.js` passes a JavaScript syntax check, and the installed Python
environment reports no broken requirements.

These checks are not stored as tests, so later changes can silently regress
them. Add a small backend test file and a basic frontend check once the app
starts changing regularly.
