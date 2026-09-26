# To-Do List: Bringing the App in Line with overview_addon.md

Comparison of the current app (`backend/main.py`, `frontend/*`) against
`overview/overview_addon.md`. Items already satisfied (CORS, input validation,
rate limiting, API key handling, error handling) are not repeated here.

## 1. Backend: return suggested links with each response

`overview_addon.md` frontend section item 7-9 requires that a valid response
include up to 3 suggested website links. The backend response model currently
only returns `{"response": "..."}` with no link data.

- [x] Use one structured model response to select an AEC category. Keep URLs
      in a static backend registry rather than accepting model-generated URLs.
- [x] Extend `ChatResponse` with `category` and `resources` fields.
- [x] Store HTTPS-only resource URLs in the backend registry.
- [x] Map every AEC category to exactly 3 resources.
- [x] If the question is off-topic (non-AEC), return no links, matching the
      "brief refusal" behavior already in the system prompt.


## 4. Frontend: display suggested links in the chat UI

Requirements 7-9: show up to 3 suggested links per valid response, open in a
new tab, HTTPS only.

- [x] Update `addMessage` (or add a new rendering function) to render a list
      of link chips/buttons under a bot message when `links` are present.
- [x] Set `target="_blank"` and `rel="noopener noreferrer"` on generated link
      elements (security best practice for new-tab links).
- [x] Guard against non-HTTPS URLs client-side too, as defense in depth (even
      though backend should already filter these).
