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
user text input
send button
hosted on my github pages

# backend on Render
backend is written in python with FastAPI
one endpoint: POST/chat
receives message such as:
{"message": "How many parking spaces fit in 40,000 sf?"}
calls openai
returns:
{"response": "..."}

# openai integration
api key stored as a Render environment variable
never expose it in frontend JavaScript
example code:
try:
    with open('secrets.txt', 'r') as f:
        api_key = f.read().strip()
except FileNotFoundError:
    api_key = os.environ.get('OPENAI_API_KEY')

For the deployed version, use the Render environment variable as the primary method.

# response to user input
when the user is not asking about aec related question, be very brief and tell them this chatbot is for work
if user asks about aec domain knowledge, explain professionally

# input validation
be sure to handle:
1. empty input by user
2. message longer than 200 words
3. handle api errors
4. return proper http erros

# cors
make sure Render backend have CORS configuration

# implementation steps
need to be locally tested first before deploying

# general comment
when faced with a decision, ask me first instead of implement random logic
Keep the implementation minimal. Do not add a database, authentication, LangChain, agents, or extra abstractions unless I ask.

# requirements.txt
Render requires a requirement.txt file that would take into account of which library needs to be installed

