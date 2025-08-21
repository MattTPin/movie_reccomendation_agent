# models.py
from typing import List, Type, Optional
from pydantic import BaseModel, Field, model_validator

from agent.utils.model_utils import *

class Person(BaseModel):
    name: str
    age: int
    gender: str
    

class Movie(BaseModel):
    """
    Model for getting information about a specific movie that a user has followed up about.
    """
    # Core required fields
    title: str = Field(example="Inception")

    # Core optional fields with defaults
    original_title: Optional[str] = Field(default=None, example="Inception")
    tagline: Optional[str] = Field(default=None, example='Your mind is the scene of the crime.')
    runtime: Optional[int] = Field(default=None, example=148)
    genres: Optional[List[str]] = Field(default=None, example=['action', 'adventure', 'science-fiction'])
    subgenres: Optional[List[str]] = Field(default=None, example=['heist', 'virtual-reality'])
    description: Optional[str] = Field(default=None, example="A thief steals secrets from dreams.")
    related: Optional[List[str]] = Field(default=None, example=["Interstellar", "Tenet"])
    franchise: Optional[List[str]] = Field(default=None, example=None)
    age_rating: Optional[str] = Field(default=None, example="PG-13")
    country: Optional[str] = Field(default=None, example="us")
    after_credits_scene: Optional[bool] = Field(default=None, example=False)
    during_credits_scene: Optional[bool] = Field(default=None, example=False)

    # Credits & personnel
    year: Optional[int] = Field(default=None, example=2010)
    release_date: Optional[str] = Field(default=None, example="2010-07-16")
    cast: Optional[List[str]] = Field(default=None, example=["Leonardo DiCaprio"])
    characters: Optional[List[str]] = Field(default=None, example=["Dom Cobb"])
    director: Optional[str] = Field(default=None, example="Christopher Nolan")
    music_by: Optional[str] = Field(default=None, example="Hans Zimmer")
    cinematographer: Optional[str] = Field(default=None, example="Wally Pfister")
    produced_by: Optional[List[str]] = Field(default=None, example=["Emma Thomas"])
    written_by: Optional[List[str]] = Field(default=None, example=["Christopher Nolan"])
    production_companies: Optional[List[str]] = Field(default=None, example=["Syncopy"])

    # Financials & performance
    budget: Optional[int] = Field(default=None, example=160000000)
    revenue: Optional[int] = Field(default=None, example=825532764)
    box_office_domestic: Optional[int] = Field(default=None, example=292576195)
    box_office_worldwide: Optional[int] = Field(default=None, example=825532764)

    # Streaming
    streaming_on: Optional[List[str]] = Field(default=None, example=["Netflix", "YouTube"])

    # Trakt
    trakt_id: Optional[int] = Field(default=None, example=16662)
    trakt_rating: Optional[float] = Field(default=None, example=8.8)
    trakt_votes: Optional[int] = Field(default=None, example=2000000)

    # Ratings
    rotten_tomatoes_score: Optional[float] = Field(default=None, example=87.0)
    metacritic_score: Optional[int] = Field(default=None, example=74)
    letterboxd_score: Optional[float] = Field(default=None, example=4.1)
    imdb_score: Optional[float] = Field(default=None, example=8.8)
    cinemascore: Optional[str] = Field(default=None, example="A")
    comments: Optional[list[str]] = Field(default=[], example=["Loved it!"])
    
    # Media
    poster: Optional[str] = Field(default=None, example="")
    trailer: Optional[str] = Field(default=None, example="")

    @classmethod
    def example(cls, include_optional: Optional[List[str]] = None) -> dict:
        always_include = {"title"}
        fields_to_include = always_include.union(include_optional or [])
        return build_example_dict(cls, fields_to_include)

    def get_example_from_instance(self) -> dict:
        always_include = {"title"}
        present_fields = extract_populated_optional_fields(self, always_include)
        return self.__class__.example(include_optional=present_fields)

class MovieList(BaseModel):
    movies: List[Movie] = []

    @classmethod
    def example(
        cls,
        include_optional: Optional[List[str]] = None,
        instance: Optional["MovieList"] = None
    ) -> "MovieList":
        if include_optional is None and instance is not None and instance.movies:
            present_fields = extract_populated_optional_fields(
                instance.movies[0],
                always_include={"title"}
            )
            include_optional = list(present_fields)

        movie_example_dict = Movie.example(include_optional=include_optional)
        return cls(movies=[Movie(**movie_example_dict)])

    def get_example_from_instance(self) -> "MovieList":
        if not self.movies:
            return self.__class__.example(include_optional=[])
        return self.__class__.example(instance=self)
    
    
    
# Action management models
class TraktActionResult(BaseModel):
    action_name: str                      # e.g., "add_to_list", "rate_movies"
    target_list: str                      # e.g., "watchlist", "collection", "ratings"
    action_success: bool
    successfully_updated_titles: List[str]
    non_updated_error_titles: List[str]
    message: str
    details: Optional[dict] = None        # optional raw API response or extra context