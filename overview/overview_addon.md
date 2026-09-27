# overall view of the app
this is a small chatbot app that helps answer aec related question

# architecture of the app
GitHub Pages / Portfolio
        |
        | fetch POST /chat
        v
Render Python Backend
        |
        | OpenAI API request
        v
     OpenAI
        |
        v
Render returns JSON
        |
        v
Frontend displays answer

# frontend chat ui
frontend has:
1: user text input
2: send button
3: Send button and input are disabled while waiting.
4: hosted on my github pages
5: while it is getting response from backend, display a Thinking… indicator and disable duplicate submissions.
6: Remove the Thinking… indicator on success or failure.
7: at each response display suggestion linked website
8: Open links in a new tab and use only HTTPS addresses
9: Suggest 3 maximum website at most

# aesthetic 
css:
1: implement a basic aesthetic for the app
2: the color palette is the following:
Primary: dark navy
Secondary: blueprint blue
Accent: safety orange
Background: light blue-gray
Message surfaces: white and pale blue


# backend on Render
backend is written in python with FastAPI
one endpoint: POST/chat
receives message such as:
{"message": "How many parking spaces fit in 40,000 sf?"}
calls openai
returns:
{
  "response": "...",
  "category": "structures",
  "resources": [
    {"title": "ASCE Codes and Standards", "url": "https://..."}
  ]
}

# aec classification and related resources
1: use one structured OpenAI response to classify and answer the question
2: valid categories are codes, safety, architecture, structures, energy,
building_systems, construction, materials, sustainability, and general_aec
3: use not_aec when the question is outside architecture, engineering,
construction, infrastructure, planning, or the built environment
4: architecture includes architects, architecture firms, notable practices,
and notable buildings
5: use needs_clarification when a name or phrase could plausibly be AEC-related
but is too ambiguous to identify confidently
6: the backend owns the resource URLs; the model returns a category, not URLs
7: each AEC category maps to exactly 3 curated HTTPS resources
8: off-topic and clarification responses receive no resources



# openai integration
api key stored as a Render environment variable
never expose it in frontend JavaScript

For internal testing version:
example code:
try:
    with open('secrets.txt', 'r') as f:
        api_key = f.read().strip()
except FileNotFoundError:
    api_key = os.environ.get('OPENAI_API_KEY')

For the deployed version, use the Render environment variable as the primary method.

# response to user input
1. when the user is not asking about aec related question, be very brief and tell them this chatbot is for work
2. if user asks about aec domain knowledge, explain professionally
3. if there is a valid response, make sure on the side, there are links user can click into relevant website

# input validation
be sure to handle:
1. empty input by user
2. message longer than 200 words
3. handle api errors
4. return proper http errors

# cors
make sure Render backend have CORS configuration

# general comment
when faced with a decision, ask me first instead of implement random logic
Keep the implementation minimal. Do not add a database, authentication, LangChain, agents, or extra abstractions unless I ask.

# requirements.txt
Render requires a requirement.txt file that would take into account of which library needs to be installed

