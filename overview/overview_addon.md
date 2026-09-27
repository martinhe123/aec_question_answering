# Overall View of the App

This is a small chatbot application that answers questions related to
architecture, engineering, and construction (AEC). It is also an experimental
project for testing structured LLM output, classification, curated resources,
deployment, validation, and conversational memory before applying those ideas
to a larger project.

# Architecture of the App

```text
GitHub Pages frontend
        |
        | POST /chat
        v
Render FastAPI backend
        |
        | validate input and assemble conversation context
        v
OpenAI API
        |
        | structured category and answer
        v
Backend attaches curated resources
        |
        v
Frontend displays the answer, category, and links
```

The backend is divided into these layers:

- `main.py`: FastAPI application, validation, rate limiting, and OpenAI call
- `schemas.py`: request, response, category, and resource models
- `prompts.py`: system prompt and fixed responses
- `resources.py`: curated resource mappings owned by the application
- `conversation_store.py`: thread-safe, temporary storage for recent messages
- `chat_service.py`: conversation assembly, OpenAI call, and response creation

# Frontend Chat UI

The frontend has:

1. A user text input and Send button.
2. A 200-word input limit.
3. A Thinking indicator while waiting for the backend.
4. Disabled input and Send button while a request is active, preventing
   duplicate submissions.
5. Removal of the Thinking indicator after success or failure.
6. A category label for valid AEC responses.
7. Up to three related resource links for each valid AEC response.
8. HTTPS-only resource links that open in a new tab using safe link attributes.
9. Hosting through GitHub Pages.
10. Reuse of the active conversation ID within the current page session.
11. A New conversation button that clears the displayed chat and starts with an
    empty history.

# Aesthetic

The interface uses a simple AEC-inspired palette:

- Primary: dark navy
- Secondary: blueprint blue
- Accent: safety orange
- Background: light blue-gray
- Message surfaces: white and pale blue

# Backend on Render

The backend is written in Python with FastAPI and is hosted on Render.

The current endpoint is `POST /chat`.

Current request:

```json
{
  "message": "How many parking spaces fit in 40,000 square feet?"
}
```

Current response:

```json
{
  "conversation_id": "generated-conversation-id",
  "response": "...",
  "category": "general_aec",
  "resources": [
    {
      "title": "Whole Building Design Guide",
      "url": "https://www.wbdg.org/"
    },
    {
      "title": "AIA Resource Center",
      "url": "https://www.aia.org/resource-center"
    },
    {
      "title": "ASCE Codes and Standards",
      "url": "https://www.asce.org/publications-and-news/codes-and-standards"
    }
  ]
}
```

# AEC Classification and Related Resources

1. Use one structured OpenAI response to classify and answer each question.
2. Valid AEC categories are `codes`, `safety`, `architecture`, `structures`,
   `energy`, `building_systems`, `construction`, `materials`,
   `sustainability`, and `general_aec`.
3. Use `not_aec` when the question is outside architecture, engineering,
   construction, infrastructure, planning, or the built environment.
4. The architecture category includes architects, architecture firms, notable
   practices, and notable buildings.
5. Use `needs_clarification` when a name or phrase could plausibly be
   AEC-related but is too ambiguous to identify confidently.
6. The backend owns all resource URLs. The model returns a category and answer,
   but it does not select or generate resource URLs.
7. Each AEC category maps to exactly three curated HTTPS resources.
8. Off-topic and clarification responses receive no resources.
9. Conversation context must be considered when classifying follow-up questions.
   For example, "What about its fire resistance?" may depend on the preceding
   discussion to determine both its subject and category.

# Conversational Memory Requirement

Conversational memory is implemented as short-term conversation context, not
permanent knowledge about the user.

1. A conversation must have a backend-generated unique `conversation_id`.
2. The first request may omit `conversation_id`. The backend then creates one
   and includes it in the response.
3. The frontend retains the returned ID and sends it with every later message
   in that conversation.
4. The application stores user and assistant messages separately and preserves
   their roles and chronological order.
5. Before calling OpenAI, the backend loads no more than the 10 most recent
   previous messages for that conversation.
6. One user entry or one assistant entry counts as one message. Therefore, 10
   previous messages normally represent five complete exchanges.
7. The current user message is added after those 10 previous messages. The
   system prompt does not count toward the 10-message limit.
8. The OpenAI request is assembled in this order:

   - system prompt
   - up to 10 previous conversation messages, oldest to newest
   - current user message

9. The same context is used for both AEC classification and answer generation,
   preserving the existing single structured OpenAI call.
10. After a successful response, the backend stores both the current user
   message and the final assistant response shown in the UI.
11. Failed API responses and validation errors are not stored as assistant
    messages.
12. Messages from one conversation must never be included in another
    conversation.
13. Starting a new conversation creates a new ID and an empty history.
14. This first version does not summarize older messages and does not provide
    cross-conversation or long-term user memory.
15. If the first implementation uses temporary in-memory storage, losing
    history after a Render restart is acceptable but must be documented. A
    database is required later for durable history across restarts and devices.

First request:

```json
{
  "message": "What is mass timber?"
}
```

Follow-up request:

```json
{
  "conversation_id": "generated-conversation-id",
  "message": "What about its fire resistance?"
}
```

Response:

```json
{
  "conversation_id": "generated-conversation-id",
  "response": "...",
  "category": "materials",
  "resources": [
    {
      "title": "NIST Buildings and Construction",
      "url": "https://www.nist.gov/buildings-and-construction"
    },
    {
      "title": "USDA Forest Products Laboratory",
      "url": "https://www.fpl.fs.usda.gov/"
    },
    {
      "title": "American Concrete Institute",
      "url": "https://www.concrete.org/"
    }
  ]
}
```

The backend returns `conversation_id` on every successful response so the
frontend can reliably continue the correct conversation.

# OpenAI Integration

1. Store the API key in the `OPENAI_API_KEY` Render environment variable.
2. Never expose the API key in frontend JavaScript.
3. For local development only, allow `backend/secrets.txt` as a fallback. This
   file must remain excluded from Git.
4. Use the environment variable as the primary source and the local file only
   when the environment variable is absent.
5. The model must return the application-defined structured `ModelResult`
   containing an `AECCategory` and answer.

# Response to User Input

1. For a clearly non-AEC question, briefly explain that the chatbot is limited
   to architecture, engineering, and construction.
2. For an AEC domain question, answer professionally and clearly.
3. For an ambiguous but potentially AEC-related question, ask for
   clarification.
4. For a valid AEC answer, display the category and curated related resources.
5. Use recent conversation context to resolve references and follow-up
   questions, but do not allow previous context to override the current user's
   clear intent.

# Input Validation and Error Handling

The application must handle:

1. Empty input.
2. Messages longer than 200 words.
3. Invalid conversation IDs or malformed conversation history.
4. OpenAI API errors and unusable model responses.
5. Proper HTTP error status codes and user-friendly frontend messages.
6. Rate limiting for the public endpoint.

# CORS

The Render backend must allow the deployed GitHub Pages origin and the approved
local development origins. CORS is browser access control; it is not a form of
authentication.

# Testing Requirements

Tests should cover:

1. Valid AEC classification and resources.
2. Off-topic and clarification responses.
3. Empty and oversized input.
4. Exactly three HTTPS resources for every AEC category.
5. A follow-up question using facts from previous messages.
6. Only the 10 most recent previous messages being sent to OpenAI.
7. Correct chronological ordering of those messages.
8. Isolation between different conversation IDs.
9. Failed requests not creating assistant-history entries.

# General Comment

Keep the implementation minimal. Do not add authentication, LangChain, agents,
or unrelated abstractions unless requested. Conversational memory is now in
scope, but durable database storage is a separate decision unless explicitly
requested.

When a requirement would materially change the architecture or user experience,
confirm the decision before implementing it.

# Requirements File

Render uses `backend/requirements.txt` to install the Python libraries required
by the application.
