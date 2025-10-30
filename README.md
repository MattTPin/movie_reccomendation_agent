# Agentic AI Chatbot for Trakt.tv

This project is an **AI-powered agentic chatbot** built with LangChain and Pydantic AI, designed to help you manage your [Trakt.tv](https://trakt.tv/) account effortlessly.

With natural language commands, you can search for movies, retrieve detailed information, and update your Trakt.tv watchlist seamlessly.

[Watch the demo video](https://youtu.be/tgt72iw6b3k)  
[![Watch the demo](https://img.youtube.com/vi/iJgqI5_qwdc/hqdefault.jpg)](https://www.youtube.com/watch?v=iJgqI5_qwdc)

## Project Setup Guide

This project requires API credentials for Trakt.tv and an Anthropic API key (for use with LangChain).

Follow the steps below to obtain the necessary API keys, set up your environment, and run the application locally.

### Environment Variables

You will need the following variables in your `.env` file. You can copy the contents of `.env.template` and replace the values with your own.

```
# TRAKT.TV
TRAKT_URL=https://api.trakt.tv
TRAKT_CLIENT_ID=<your_trakt_client_id>
TRAKT_CLIENT_SECRET=<your_trakt_client_secret>
TRAKT_ACCESS_TOKEN=<your_trakt_access_token>

# LangChain API model / Keys
ANTHROPIC_API_KEY=<REPLACE_ME>
ANTHROPIC_MODEL_ID=claude-sonnet-4-5-20250929
```

## Local (Manual) Setup

### API KEYS

1. Obtain API Keys (for use with LangChain + Anthropic)

### Trakt.tv

#### Create an Account
1. Create a free account at https://trakt.tv/
2. Go to https://trakt.tv/oauth/applications
3. Click "New Application" and fill out:
   - Name: anything you like (e.g., MyApp)
   - Redirect URI: http://localhost:8080
4. After saving, you’ll get:
   - Client ID → TRAKT_CLIENT_ID
   - Client Secret → TRAKT_CLIENT_SECRET

#### Get an Access Token
1. Open this URL in your browser (replace `<CLIENT_ID>`):

- `https://trakt.tv/oauth/authorize?response_type=code&client_id=<CLIENT_ID>&redirect_uri=http://localhost:8080`


2. Approve access when prompted.

3. You’ll be redirected to:

- `http://localhost:8080/?code=<CODE>`

- Copy the value of `<CODE>` → this is your Authorization Code

4. Exchange it for an Access Token with this command:

```
curl -X POST "https://api.trakt.tv/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "<ACCESS_CODE>",
    "client_id": "<TRAKT_CLIENT_ID>",
    "client_secret": "<TRAKT_CLIENT_SECRET>",
    "redirect_uri": "http://localhost:8080",
    "grant_type": "authorization_code"
  }'
```

5. The response will contain:

```
{
"access_token": "<YOUR_TRAKT_ACCESS_TOKEN>",
"token_type": "bearer",
"expires_in": 7889238,
...
}
```

- Copy `"access_token"` → TRAKT_ACCESS_TOKEN

## Configure and Run Project
 
### 1. Clone the repo:
```bash
git clone https://github.com/MattTPin/movie_reccomendation_agent
cd movie_reccomendation_agent
```

### 2. Create a .env file:
# Copy .env.template → .env
# Paste your credentials into .env


### 3. Create a virtual environment (recommended: venv):
```bash
python3 -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows
```

### 4. Install dependencies:
```bash
pip install -r requirements.txt
```

### 5. Run the app:
```bash
python app.py
```

### 6. Open your browser and go to `http://127.0.0.1:7860`
The chatbot should now be running. Access it in your internet browser!

## Features & Actions

The chatbot can perform several key actions when prompted with natural language, interfacing with the **Trakt.tv API** to generate accurate responses:

### `GetTrending`
- **Description**: Get a list of current popular movies.

### `GetDetails`
- **Description**: Get detailed information about a specific movie.

### `GetSimilar`
- **Description**: Get movies similar to a provided title.

### `GetUserList`
- **Description**: Retrieve user-specific lists from Trakt.tv (e.g., watchlist, ratings, history).  
- **Args**:  
- `list_type (str, required)` → one of `['watchlist','collection','ratings','history']`.

### `AddOrRemoveFromWatchList`
- **Description**: Update the user’s Trakt.tv watchlist by adding or removing a single movie.