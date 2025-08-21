# test_get_trakt_list.py

import sys
import os
import pytest
import time
from typing import List, Dict

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from agent.models import MovieList, Movie
from agent.logic.services.trakt.trakt_lists import query_user_trakt_list
from agent.logic.services.trakt.get_movies import query_trakt_movie

# Constants for test movies
INCEPTION_TRAKT_ID = 16662
INCEPTION_TITLE = "Inception"
BATMAN_BEGINS_ID = 228
BATMAN_BEGINS_TITLE = "Batman Begins"

class TestQueryUserTraktList:

    def test_fetch_watchlist(self):
        """Fetch movies from the user's watchlist."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(list_type="watchlist", limit=5)
        assert isinstance(movie_list, MovieList)
        assert len(movie_list.movies) <= 5
        for movie in movie_list.movies:
            assert isinstance(movie, Movie)
            assert movie.title

    def test_fetch_collection(self):
        """Fetch movies from the user's collection."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(list_type="collection", limit=5)
        assert isinstance(movie_list, MovieList)
        for movie in movie_list.movies:
            assert isinstance(movie, Movie)
            assert movie.trakt_id is not None

    def test_fetch_ratings(self):
        """Fetch movies the user has rated."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(list_type="ratings", limit=5)
        assert isinstance(movie_list, MovieList)
        for movie in movie_list.movies:
            assert isinstance(movie, Movie)
            assert hasattr(movie, "user_rating")

    def test_fetch_history(self):
        """Fetch movies from the user's watch history."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(list_type="history", limit=5)
        assert isinstance(movie_list, MovieList)
        for movie in movie_list.movies:
            assert isinstance(movie, Movie)

    def test_fetch_comments(self):
        """Fetch movies the user has commented on."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(list_type="comments", limit=5)
        assert isinstance(movie_list, MovieList)
        for movie in movie_list.movies:
            assert isinstance(movie, Movie)

    def test_limit_exceeds_max(self):
        """Verify that the limit argument is capped at 100."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(list_type="watchlist", limit=150)
        assert len(movie_list.movies) <= 100

    def test_empty_list(self):
        """Handle case where the user has no movies in a list."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(list_type="watchlist", limit=1)
        assert isinstance(movie_list, MovieList)
        assert isinstance(movie_list.movies, list)

    # -----------------------------
    # New filtering & sorting tests
    # -----------------------------
    def test_filter_by_genres(self):
        """Filter watchlist by one or more genres."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(
            list_type="watchlist",
            genres=["action", "sci-fi"],
            limit=20
        )
        for movie in movie_list.movies:
            assert any(g.lower() in ["action", "sci-fi"] for g in movie.genres)

    def test_filter_by_cast_member(self):
        """Filter by a specific cast member."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(
            list_type="watchlist",
            cast_member="Leonardo DiCaprio",
            limit=20
        )
        for movie in movie_list.movies:
            assert any("leonardo dicaprio" in c.lower() for c in movie.cast)

    def test_filter_by_director(self):
        """Filter by director name."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(
            list_type="watchlist",
            director_name="Christopher Nolan",
            limit=20
        )
        for movie in movie_list.movies:
            assert movie.director and "christopher nolan" in movie.director.lower()

    def test_filter_by_runtime_range(self):
        """Filter by runtime between 100 and 150 minutes."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(
            list_type="watchlist",
            runtime_range=(100, 150),
            limit=20
        )
        for movie in movie_list.movies:
            assert 100 <= movie.runtime <= 150

    def test_filter_by_year_range(self):
        """Filter by release year between 2000 and 2020."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(
            list_type="watchlist",
            year_range=(2000, 2020),
            limit=20
        )
        for movie in movie_list.movies:
            if movie.release_date:
                year = int(movie.release_date.split("-")[0])
                assert 2000 <= year <= 2020

    def test_filter_by_score_cutoff(self):
        """Filter by minimum Trakt score of 7.0."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(
            list_type="watchlist",
            score_cutoff=7.0,
            limit=20
        )
        for movie in movie_list.movies:
            assert movie.trakt_rating is None or movie.trakt_rating >= 7.0

    def test_sort_by_trakt_rating(self):
        """Ensure sorting by trakt_rating works."""
        time.sleep(1.5)
        movie_list = query_user_trakt_list(
            list_type="watchlist",
            sort_by="trakt_rating",
            limit=20
        )
        ratings = [m.trakt_rating or 0 for m in movie_list.movies]
        assert ratings == sorted(ratings, reverse=True)