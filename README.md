# Agentic AI Chatbot for Trakt.tv

This project is an **AI-powered agentic chatbot** that helps you manage your [Trakt.tv](https://trakt.tv/) account.  
With natural language commands, you can search for movies, get details, and update your Trakt.tv watchlist seamlessly.

[Watch the demo video](https://www.youtube.com/watch?v=iJgqI5_qwdc)  
[![Watch the demo](https://img.youtube.com/vi/iJgqI5_qwdc/hqdefault.jpg)](https://www.youtube.com/watch?v=iJgqI5_qwdc)

---

## Features & Actions

The chatbot can perform several key actions when prompted with natural language that see it interfacing with the **Trakt.tv API** to generate a response with accurate information:

### `GetTrending`
- **Description**: Get a list of current popular movies.
---

### `GetDetails`
- **Description**: Get detailed information about a specific movie.  

---

### `GetUserList`
- **Description**: Retrieve user-specific lists from Trakt.tv (e.g., watchlist, ratings, history).  
- **Args**:  
  - `list_type (str, required)` → one of `['watchlist','collection','ratings','history']`.  

---

### `AddOrRemoveFromWatchList`
- **Description**: Update the user’s Trakt.tv watchlist by adding or removing a single movie.  
---
