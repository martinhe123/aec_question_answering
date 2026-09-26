# To-Do List: Bringing the App in Line with overview_addon.md

Comparison of the current app (`backend/main.py`, `frontend/*`) against
`overview/overview_addon.md`. Items already satisfied (CORS, input validation,
rate limiting, API key handling, error handling) are not repeated here.

## 1. Backend: return suggested links with each response

`overview_addon.md` frontend section item 7-9 requires that a valid response
include up to 3 suggested website links. The backend response model currently
only returns `{"response": "..."}` with no link data.

- [ ] Decide how links are produced (ask before implementing): either have the
      model suggest relevant AEC resource URLs as part of its answer (e.g. via
      an extended system prompt asking it to return links in a structured
      way), or maintain a small static/curated list matched by keyword. Given
      "Keep the implementation minimal" and "ask me first instead of
      implementing random logic," this needs your decision before coding.
- [ ] Extend `ChatResponse` model to include a `links` field: a list of at
      most 3 items, each with a URL (and optionally a label).
- [ ] Validate/filter that every returned link is `https://` only (drop or
      reject anything else, per requirement 8).
- [ ] Cap the list at 3 links even if more are produced.
- [ ] If the question is off-topic (non-AEC), return no links, matching the
      "brief refusal" behavior already in the system prompt.

## 2. Frontend: disable input (not just the button) while waiting

Requirement 3 says both the Send button *and* the input field should be
disabled while waiting for a response.

- [ ] In `script.js`, set `chatInput.disabled = true` alongside
      `sendButton.disabled = true` when a request starts, and re-enable both
      in the `finally` block.

## 3. Frontend: "Thinking…" indicator

Requirements 5-6: show a "Thinking…" indicator while waiting for the backend,
and remove it on success or failure.

- [ ] Add a transient bot-style message (or a dedicated indicator element)
      showing "Thinking…" right after the user's message is added.
- [ ] Remove/replace that indicator once the response arrives, whether it
      succeeds or errors out.

## 4. Frontend: display suggested links in the chat UI

Requirements 7-9: show up to 3 suggested links per valid response, open in a
new tab, HTTPS only.

- [ ] Update `addMessage` (or add a new rendering function) to render a list
      of link chips/buttons under a bot message when `links` are present.
- [ ] Set `target="_blank"` and `rel="noopener noreferrer"` on generated link
      elements (security best practice for new-tab links).
- [ ] Guard against non-HTTPS URLs client-side too, as defense in depth (even
      though backend should already filter these).

## 5. CSS: apply the specified color palette

Requirement: implement the palette below (currently the app uses generic
blue `#0b6efd` / gray tones, not this palette).

- Primary: dark navy
- Secondary: blueprint blue
- Accent: safety orange
- Background: light blue-gray
- Message surfaces: white and pale blue

- [ ] Define CSS custom properties (`:root { --primary: ...; }`) for each
      palette color with concrete hex values (need to pick/confirm exact
      hexes, e.g. navy `#0a1f44`, blueprint blue `#1e5aa8`, safety orange
      `#ff6a13`, light blue-gray background `#eef2f6`, pale blue message
      surface `#e3edf7`) — confirm exact shades with you before finalizing.
- [ ] Apply primary (dark navy) to header/title text and user message
      bubbles or send button.
- [ ] Apply secondary (blueprint blue) to accents like focus outlines, links,
      borders.
- [ ] Apply accent (safety orange) sparingly for calls to action (e.g. hover
      state, indicator, or link highlight) — small doses per "accent" role.
- [ ] Set page background to light blue-gray.
- [ ] Set message bubble surfaces to white (user or bot) and pale blue (the
      other), replacing current `#0b6efd` / `#e9e9eb`.

## 6. Optional cleanup carried over from issues.md (not required by addon, but worth noting)

Not part of `overview_addon.md`, but flagged during review — mention only,
not required unless you want them bundled in:

- [ ] Add a request timeout / `AbortController` so a slow OpenAI call doesn't
      hang the UI indefinitely (issues.md item 1).
- [ ] Cap OpenAI response tokens to bound cost per request (issues.md item 2).

---

**Needs your decision before implementation:** item 1 (how links are
sourced/generated) and the exact hex values in item 5. Everything else can be
implemented directly once you give the go-ahead.
