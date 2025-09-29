# Agentic AI Chatbot for Trakt.tv

This project is an **AI-powered agentic chatbot** that helps you manage your [Trakt.tv](https://trakt.tv/) account.  
With natural language commands, you can search for movies, get details, and update your Trakt.tv watchlist seamlessly.

[Watch the demo video](https://youtu.be/tgt72iw6b3k)  
[![Watch the demo](https://img.youtube.com/vi/iJgqI5_qwdc/hqdefault.jpg)](https://www.youtube.com/watch?v=iJgqI5_qwdc)

---

# Project Setup Guide

This project requires API credentials for Trakt.tv and AWS (Bedrock).
Follow the steps below to obtain the necessary API keys, set up your environment, and run the application locally.

--------------------------------------------------------------------
Environment Variables

You will need the following variables in your .env file:

```
# TRAKT.TV
TRAKT_URL=https://api.trakt.tv
TRAKT_CLIENT_ID=<your_trakt_client_id>
TRAKT_CLIENT_SECRET=<your_trakt_client_secret>
TRAKT_ACCESS_TOKEN=<your_trakt_access_token>

# AWS SETUP
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=<your_aws_access_key_id>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_access_key>

# BEDROCK MODEL SELECTION
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
```

## Local Setup
1. Obtain API Keys

=== AWS Bedrock ===
1. Log into your AWS Console: https://console.aws.amazon.com/
2. Apply for Bedrock access (if not already enabled) and request access to:
   anthropic.claude-3-haiku-20240307-v1:0
3. Go to IAM → Users → Security credentials
4. Create a new Access Key with permissions for Bedrock
   - Copy the Access Key ID → AWS_ACCESS_KEY_ID
   - Copy the Secret Access Key → AWS_SECRET_ACCESS_KEY
5. Set your AWS region (default: us-west-2) → AWS_REGION

=== Trakt.tv ===
1. Create a free account at https://trakt.tv/
2. Go to https://trakt.tv/oauth/applications
3. Click "New Application" and fill out:
   - Name: anything you like (e.g., MyApp)
   - Redirect URI: http://localhost:8080
4. After saving, you’ll get:
   - Client ID → TRAKT_CLIENT_ID
   - Client Secret → TRAKT_CLIENT_SECRET

--- Get Your Access Token ---
1. Open this URL in your browser (replace <CLIENT_ID>):
   https://trakt.tv/oauth/authorize?response_type=code&client_id=<CLIENT_ID>&redirect_uri=http://localhost:8080

2. Approve access when prompted.

3. You’ll be redirected to:
   - http://localhost:8080/?code=`<CODE>`
   - Copy the value of `<CODE>`→ this is your Authorization Code

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
   {
     "access_token": "<YOUR_TRAKT_ACCESS_TOKEN>",
     "token_type": "bearer",
     "expires_in": 7889238,
     ...
   }
   - Copy "access_token" → TRAKT_ACCESS_TOKEN

--------------------------------------------------------------------
2. Setup Project Locally
    1. Clone the repo:
    ```
    git clone https://github.com/MattTPin/movie_reccomendation_agent
    cd movie_reccomendation_agent
    ```

    2. Create a .env file:
    - Copy .env.template → .env
    - Paste your credentials into .env

    3. Create a virtual environment (recommended: venv):
    python3 -m venv venv
    source venv/bin/activate   # On macOS/Linux
    venv\Scripts\activate      # On Windows

    4. Install dependencies:
    pip install -r requirements.txt

    5. Run the app:
    python app.py

    6. Open your browser to:
    http://127.0.0.1:7860
    The chatbot should now be running.


## Features & Actions

The chatbot can perform several key actions when prompted with natural language that see it interfacing with the **Trakt.tv API** to generate a response with accurate information:

### `GetTrending`
- **Description**: Get a list of current popular movies.
---

### `GetDetails`
- **Description**: Get detailed information about a specific movie.  

---

### `GetSimilar`
- **Description**: Get movies similar to a provided title.

---
### `GetUserList`
- **Description**: Retrieve user-specific lists from Trakt.tv (e.g., watchlist, ratings, history).  
- **Args**:  
  - `list_type (str, required)` → one of `['watchlist','collection','ratings','history']`.  

---
### `AddOrRemoveFromWatchList`
- **Description**: Update the user’s Trakt.tv watchlist by adding or removing a single movie.  
---
