# test_edit_trakt_lists.py

import sys
import os
import pytest
import time
from typing import List, Dict

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from agent.models import TraktListActionResult
from agent.logic.services.trakt.get_movies import query_trakt_movie
from agent.logic.services.trakt.trakt_lists import update_trakt_list

# Constants for test movies
INCEPTION_TRAKT_ID = 16662
INCEPTION_TITLE = "Inception"
BATMAN_BEGINS_ID = 228
BATMAN_BEGINS_TITLE = "Batman Begins"
FAKE_MOVIE_TITLE = "ThisMovieDoesNotExistXYZ"

class TestUpdateTraktList:
    def test_add_movie_by_trakt_id(self):
        """Add a known movie to the watchlist by trakt_id."""
        time.sleep(1.5)
        result = update_trakt_list(
            movies=[{"trakt_id": INCEPTION_TRAKT_ID, "title": INCEPTION_TITLE}],
            target_list="watchlist",
            mode="add"
        )
        assert isinstance(result, TraktListActionResult)
        assert result.target_list == "watchlist"
        assert any(INCEPTION_TITLE in msg for msg in result.message.splitlines())

    # def test_add_movie_by_title(self):
    #     """Add a known movie by title (no trakt_id provided)."""
    #     time.sleep(1.5)
    #     result = update_trakt_list(
    #         movies=[{"title": BATMAN_BEGINS_TITLE}],
    #         target_list="watchlist",
    #         mode="add"
    #     )
    #     assert isinstance(result, TraktListActionResult)
    #     assert result.action_success is True
    #     assert BATMAN_BEGINS_TITLE in result.successfully_updated_titles

    # def test_remove_existing_movie(self):
    #     """Remove a movie that should exist in the watchlist."""
    #     time.sleep(1.5)
    #     # First add
    #     update_trakt_list(
    #         movies=[{"trakt_id": INCEPTION_TRAKT_ID, "title": INCEPTION_TITLE}],
    #         target_list="watchlist",
    #         mode="add"
    #     )
    #     time.sleep(1.5)
    #     # Then remove
    #     result = update_trakt_list(
    #         movies=[{"trakt_id": INCEPTION_TRAKT_ID, "title": INCEPTION_TITLE}],
    #         target_list="watchlist",
    #         mode="remove"
    #     )
    #     assert result.action_success is True
    #     assert INCEPTION_TITLE in result.successfully_updated_titles

    # def test_remove_non_existing_movie(self):
    #     """Try removing a movie not on the list."""
    #     time.sleep(1.5)
    #     result = update_trakt_list(
    #         movies=[{"trakt_id": BATMAN_BEGINS_ID, "title": BATMAN_BEGINS_TITLE}],
    #         target_list="watchlist",
    #         mode="remove"
    #     )
    #     assert result.action_success is False
    #     assert any("was not found" in msg for msg in result.message.splitlines())

    # def test_add_existing_movie(self):
    #     """Adding a movie already in the list should return 'already in list' message."""
    #     time.sleep(1.5)
    #     # Ensure it's already added
    #     update_trakt_list(
    #         movies=[{"trakt_id": INCEPTION_TRAKT_ID, "title": INCEPTION_TITLE}],
    #         target_list="watchlist",
    #         mode="add"
    #     )
    #     time.sleep(1.5)
    #     # Add again
    #     result = update_trakt_list(
    #         movies=[{"trakt_id": INCEPTION_TRAKT_ID, "title": INCEPTION_TITLE}],
    #         target_list="watchlist",
    #         mode="add"
    #     )
    #     assert any("already in your watchlist" in msg for msg in result.message.splitlines())

    # def test_handle_invalid_movie(self):
    #     """Should handle missing/invalid movies gracefully."""
    #     time.sleep(1.5)
    #     result = update_trakt_list(
    #         movies=[{"title": FAKE_MOVIE_TITLE}],
    #         target_list="watchlist",
    #         mode="add"
    #     )
    #     assert result.action_success is False
    #     assert any("Could not find" in msg for msg in result.message.splitlines())

    # def test_add_with_rating(self):
    #     """Add a movie with a rating."""
    #     time.sleep(1.5)
    #     result = update_trakt_list(
    #         movies=[{"trakt_id": INCEPTION_TRAKT_ID, "title": INCEPTION_TITLE, "rating": 9}],
    #         target_list="ratings",
    #         mode="add"
    #     )
    #     assert result.action_success is True
    #     assert any("Successfully added" in msg for msg in result.message.splitlines())
