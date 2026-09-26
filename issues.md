# Pre-Deployment Review

Reviewed on September 26, 2026 against the current files and `overview.md`.
This is a review only; no application code was changed.

## Critical

### 1. The published frontend would call the visitor's own computer

`frontend/script.js` still contains:

```javascript
const API_URL = "http://127.0.0.1:8000/chat";
```

That address works only when the frontend and backend are being tested on the
same computer. From GitHub Pages it points to each visitor's computer, so chat
requests will fail. An HTTPS page may also block the HTTP request as mixed
content.

**Required before publishing the frontend:** deploy the backend and replace the
value with its Render HTTPS endpoint, for example:

```javascript
const API_URL = "https://YOUR-SERVICE-NAME.onrender.com/chat";
```

## Medium

### 2. The Render service configuration is not recorded as code

There is no `render.yaml`. Deployment can still work, but only if the Render
dashboard is configured correctly. Because `main.py` and `requirements.txt`
are in `backend`, the expected settings are:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variable: `OPENAI_API_KEY` set to a valid key

An incorrect root directory or start command will prevent startup. Do not
upload or commit a plaintext API key.

### 3. This folder is not currently a Git repository

The folder has a `.gitignore`, but no `.git` directory. If this is the folder
that is meant to supply the GitHub Pages site, it still needs to be initialized
as a repository and connected to the intended GitHub repository, or its files
need to be copied into an existing repository. If deployment is managed from a
different repository, record that location in `overview.md` so the source of
truth is clear.

### 4. The production CORS origin must match the frontend origin

`backend/main.py` allows `https://martinhe123.github.io`. This is correct only
if the published frontend uses that scheme and hostname. A GitHub Pages
repository path is not part of the CORS origin.

If the GitHub username changes or the site uses a custom domain, update
`ALLOWED_ORIGINS` with the exact production origin or the browser will block
chat requests. The two localhost origins can remain for local testing.

### 5. Cost protection is limited

The public `/chat` endpoint requires no authentication. It has an in-memory
limit of 10 requests per client IP per minute, but that limit resets when the
service restarts and is not shared between multiple instances. Direct callers
can still consume OpenAI credits.

The OpenAI request also has no response-token limit, so a short input can still
produce a comparatively long paid response.

**Before launch:** use a dedicated OpenAI project API key, configure project
budget alerts or limits, and consider a conservative response-token limit.
Stronger shared rate limiting can wait unless the app will be broadly shared.

### 6. Requests rely on long SDK timeouts and the frontend cannot cancel them

The app does not set an intentional OpenAI timeout or retry policy. With the
currently installed OpenAI package, it inherits two retries and a 600-second
read timeout. A slow upstream request can therefore remain open much longer
than a visitor expects and may outlast the hosting platform's request timeout.
The frontend `fetch` also has no timeout, so the Send button can remain disabled
while it waits.

Set a shorter app-level timeout and return a friendly timeout response before
wider use. A matching browser-side timeout would keep the interface responsive.

## Not Urgent

### 7. The Python runtime version is not pinned

The local virtual environment uses Python 3.12, but the project does not declare
a Python version. A future hosting default change could alter dependency
behavior. Add a Render runtime setting or `.python-version` file when
reproducible deployments become important.

### 8. `allow_credentials=True` is unnecessary for this frontend

The frontend does not send cookies or browser credentials. Keeping credentials
enabled with explicit origins is not currently a vulnerability, but setting it
to `False` would describe the application's actual behavior more accurately.

### 9. The rate limiter is intended only for a tiny single-process service

Request history lives in Python memory and is keyed by the client IP visible to
the app. It is neither persistent nor shared. After deployment, confirm from
logs that separate visitors are identified as expected and are not grouped
under one proxy address.

The limiter also runs before input validation, so empty or oversized requests
use a request slot. That is acceptable for abuse protection, but it should be
intentional.

### 10. The local virtual environment is inside the project folder

`backend/.venv` contains generated dependency files. It is excluded by
`.gitignore`, so it should not be committed or deployed, but keeping it inside
the project adds storage and file-search noise. Moving it is optional.

### 11. The test client emits a dependency deprecation warning

Importing FastAPI's current `TestClient` produces a warning that the installed
Starlette test client's `httpx` integration is deprecated in favor of `httpx2`.
This does not affect the running service. Test dependency upgrades together
rather than changing one package independently.

### 12. There is no repeatable automated test suite

The health route, empty-input rejection, 200-word limit, and CORS behavior pass
local spot checks, and `frontend/script.js` is syntactically valid. However,
those checks are not stored as tests, so later changes can silently regress
them. A small backend test file and a basic frontend check would be useful once
the app starts changing regularly.
