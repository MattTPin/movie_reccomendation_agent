
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
import time
from typing import Set

from agent.logic.services.trakt.get_movies import (
    query_trakt_movie,
    query_top_trakt_movies,
    search_trakt_movie
)
from agent.models import Movie, MovieList  # adjust path to your pydantic models

# Use a known Trakt movie ID (e.g., for "Inception")
INCEPTION_TRAKT_ID = 16662 
INCEPTION_TITLE = "Inception"

BATMAN_BEGINS_ID = 228
BATMAN_BEGINS_TITLE = "Batman Begins"

# Tests for query_trakt_movie()

class TestQueryMovie:
    def test_query_trakt_movie_full_fields(self):
        """Test that full movie data is returned for a valid Trakt ID."""
        movie = query_trakt_movie(INCEPTION_TRAKT_ID)
        print("---------------MOVIE 1 is")
        print(movie)
        assert isinstance(movie, Movie)
        assert movie.title.lower() == "inception"
        assert movie.year == 2010
        assert movie.trakt_id == INCEPTION_TRAKT_ID
        assert movie.cast  # should include some cast members
        assert movie.trakt_rating is not None
        assert movie.related is not None
        time.sleep(1.5)


#     def test_query_trakt_movie_with_optional_fields(self):
#         """Test optional field inclusion."""
#         fields: Set[str] = {"genres", "trakt_rating", "description"}
#         movie = query_trakt_movie(INCEPTION_TRAKT_ID, include_specific_fields=fields)
#         print("-------------MOVIE 2 is", movie)
#         assert isinstance(movie, Movie)
#         assert movie.genres
#         assert movie.description
#         assert movie.trakt_rating is not None
#         time.sleep(1.5)
        
#     def test_query_trakt_movie_full_fields_2(self):
#         """Test optional field inclusion."""
#         movie = query_trakt_movie(BATMAN_BEGINS_ID)
#         print("------------MOVIE 3 is", movie)
#         assert isinstance(movie, Movie)
#         assert movie.genres
#         assert movie.description
#         assert movie.trakt_rating is not None
#         time.sleep(1.5)


#     def test_query_trakt_movie_invalid_id(self):
#         """Test that an invalid Trakt ID raises an error."""
#         with pytest.raises(Exception):  # requests.HTTPError or custom error if handled
#             query_trakt_movie(999_999_999)
#         time.sleep(1.5)


# Tests for query_top_trakt_movies()

class TestSearchTopMovies:
    def test_query_top_trakt_movies_trending_default(self):
        """Test default behavior of top trending movies."""
        movie_list = query_top_trakt_movies()
        assert isinstance(movie_list, MovieList)
        assert len(movie_list.movies) == 3
        assert all(isinstance(m, Movie) for m in movie_list.movies)
        
        print("----------------movie_list output is is")
        print(movie_list)
        time.sleep(1.5)


#     def test_query_top_trakt_movies_popular_5(self):
#         """Test fetching 5 popular movies."""
#         result = query_top_trakt_movies(num=5, list_type="popular")
#         assert isinstance(result, MovieList)
#         assert len(result.movies) == 5
#         for movie in result.movies:
#             assert movie.title
#             assert isinstance(movie.trakt_rating, (float, type(None)))
#         time.sleep(1.5)


#     def test_query_top_trakt_movies_anticipated_max(self):
#         """Test fetching max allowed movies (10) from anticipated list."""
#         result = query_top_trakt_movies(num=15, list_type="anticipated")
#         assert isinstance(result, MovieList)
#         assert len(result.movies) == 10  # capped at 10
#         time.sleep(1.5)


#     def test_query_top_trakt_movies_invalid_list_type(self):
#         """Test that an invalid list type raises an error."""
#         with pytest.raises(KeyError):
#             query_top_trakt_movies(list_type="notreal")
#         time.sleep(1.5)


# # Tests for search_trakt_movie()

# class TestSearchMovie:
#     def test_search_trakt_movie_found(self):
#         """Test searching for an exact match movie title."""
#         movie = search_trakt_movie("Inception")
#         assert isinstance(movie, Movie)
#         assert movie.title.lower() == "inception"
#         assert movie.year == 2010
#         assert movie.trakt_rating is not None
#         time.sleep(1.5)


#     def test_search_trakt_movie_case_insensitive(self):
#         """Test case-insensitive search."""
#         movie = search_trakt_movie("inCePtion")
#         assert isinstance(movie, Movie)
#         assert movie.title.lower() == "inception"
#         time.sleep(1.5)


#     def test_search_trakt_movie_not_found(self):
#         """Test behavior when the movie isn't found."""
#         result = search_trakt_movie("ThisMovieDoesNotExist2025")
#         assert result is None
#         time.sleep(1.5)