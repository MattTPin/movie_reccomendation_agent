# tmdb.py
import requests

from agent.config import TMDB_API_KEY

BASE_URL = "https://api.themoviedb.org/3"

# Cache genres so we can map genre_ids → names
_genre_map: dict[int, str] | None = None

def _get_genre_map() -> dict[int, str]:
    global _genre_map
    if _genre_map is None:
        resp = requests.get(f"{BASE_URL}/genre/movie/list", params={"api_key": TMDB_API_KEY})
        resp.raise_for_status()
        _genre_map = {g["id"]: g["name"] for g in resp.json().get("genres", [])}
    return _genre_map


def get_tmdb_movie(title: str) -> dict | None:
    """Search TMDb by title and return the first result dict, or None."""
    resp = requests.get(f"{BASE_URL}/search/movie", params={
        "api_key": TMDB_API_KEY,
        "query": title
    })
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def query_tmdb_trending_movies(num: int = 3) -> list[dict]:
    """
    Fetch TMDb's weekly trending movies, return up to `num` items,
    each dict containing title, year, genres, description.
    """
    resp = requests.get(f"{BASE_URL}/trending/movie/week", params={"api_key": TMDB_API_KEY})
    resp.raise_for_status()
    results = resp.json().get("results", [])[:num]

    genres_map = _get_genre_map()
    movies = []
    for r in results:
        release = r.get("release_date", "")
        year = int(release[:4]) if release and len(release) >= 4 else None
        movies.append({
            "title": r.get("title") or r.get("name", ""),
            "year": year,
            "genres": [genres_map.get(gid, "") for gid in r.get("genre_ids", [])],
            "description": r.get("overview", ""),
        })
    return movies

