import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from agent.models import Movie, MovieList, generate_system_prompt_from_model_instance

BASE_PROMPT = """
    You are a test assistant.

    You will be provided with a json like this.
    {+json+}
"""

class TestMovie:
    def test_example_includes_only_specified_fields(self):
        example = Movie.example(include_optional=["cast", "director"])
        print("Example Movie is", example)
        assert "title" in example
        assert "cast" in example
        assert "director" in example
        assert "budget" not in example  # not included

    def test_example_defaults_to_core_fields(self):
        example = Movie.example()
        assert "title" in example
        # Optional fields excluded unless explicitly requested
        assert "cast" not in example
        assert "cinematographer" not in example

    def test_get_example_from_instance_includes_present_fields(self):
        instance = Movie(
            title="Inception",
            genres=["Sci-Fi"],
            description="Dream heist.",
            year=2010,
            director="Christopher Nolan",
            imdb_score=8.8
        )
        example = instance.get_example_from_instance()
        assert "title" in example
        assert "director" in example
        assert "imdb_score" in example
        assert "budget" not in example


class TestMovieList:
    def test_example_passes_fields_to_movie(self):
        movielist = MovieList.example(include_optional=["cast", "cinematographer"])
        assert isinstance(movielist, MovieList)
        movie = movielist.movies[0]
        assert movie.cast is not None
        assert movie.cinematographer is not None
        assert movie.box_office_domestic is None

    def test_get_example_from_instance(self):
        instance = MovieList(movies=[
            Movie(
                title="Inception",
                director="Christopher Nolan",
                music_by="Hans Zimmer"
            )
        ])
        example_list = instance.get_example_from_instance()
        movie = example_list.movies[0]
        assert movie.title == "Inception"
        assert movie.director == "Christopher Nolan"
        assert movie.music_by == "Hans Zimmer"
        assert movie.trakt_rating is None


class TestPromptGeneration:
    def test_generate_system_prompt_from_model_instance_from_movie(self):
        instance = Movie(
            title="Inception",
            description="Dream heist.",
            genres=["Sci-Fi"]
            # No optional fields
        )
        prompt = generate_system_prompt_from_model_instance(BASE_PROMPT, instance)
        assert "Inception" in prompt
        assert "description" in prompt
        assert "cast" not in prompt

    def test_generate_system_prompt_from_model_instance_from_movielist(self):
        instance = MovieList(movies=[
            Movie(
                title="Inception",
                description="Dream heist.",
                genres=["Sci-Fi"],
                cast=["Leonardo DiCaprio"]
            )
        ])
        prompt = generate_system_prompt_from_model_instance(BASE_PROMPT, instance)
        print("REPLACEMENT PROMPT 2 IS")
        print(prompt)
        assert "Inception" in prompt
        assert "cast" in prompt
        assert "cinematographer" not in prompt