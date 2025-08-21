"""Tests for retrieving current top story using Top Stories and Items APIs."""

import pytest
from pydantic import BaseModel, Field, ValidationError


class StoryItem(BaseModel):
    """Schema for a story item from Items API."""

    id: int = Field(..., gt=0)
    type: str = Field(..., pattern="^story$")
    by: str = Field(..., min_length=1)
    time: int = Field(..., gt=0)
    title: str = Field(..., min_length=1)
    score: int = Field(..., ge=0)
    descendants: int = Field(..., ge=0)
    url: str | None = Field(default=None)
    text: str | None = Field(default=None)
    kids: list[int] | None = Field(default=None)


@pytest.fixture(scope="module")
def top_story_id(hackernews_api):
    """Fixture that returns the current top story ID from Top Stories API.

    Args:
        hackernews_api: HackerNews API client fixture

    Returns:
        int: The ID of the current top story
    """
    # Get the first (top) story from the top stories list
    top_stories = hackernews_api.get_top_stories(limit=1)
    assert len(top_stories) == 1, "Expected exactly one top story"
    assert isinstance(top_stories[0], int), "Top story ID should be an integer"
    assert top_stories[0] > 0, "Top story ID should be positive"

    return top_stories[0]


# =============================================================================
# API CONTRACT VALIDATION TESTS
# =============================================================================


def test_current_top_story_response_code_200(hackernews_api, top_story_id):
    """Test that retrieving current top story returns HTTP 200."""
    hackernews_api.get_item(top_story_id)

    status_code = hackernews_api.get_status_code()
    assert status_code == 200


def test_current_top_story_response_headers(hackernews_api, top_story_id):
    """Test that current top story endpoint returns appropriate headers."""
    hackernews_api.get_item(top_story_id)

    headers = hackernews_api.get_headers()

    # Verify essential headers exist
    assert headers is not None
    assert "Content-Type" in headers

    # Content type should be JSON
    content_type = headers["Content-Type"].lower()
    assert "application/json" in content_type


def test_current_top_story_schema_validation(hackernews_api, top_story_id):
    """Test that current top story response matches expected schema using Pydantic."""
    story = hackernews_api.get_item(top_story_id)

    # Validate story structure using Pydantic model (covers required fields and types)
    try:
        validated_story = StoryItem(**story)
        assert validated_story.id == top_story_id
        assert validated_story.type == "story"
        assert len(validated_story.title) > 0
        assert validated_story.score >= 0
    except ValidationError as e:
        pytest.fail(f"Story schema validation failed: {e}")


# =============================================================================
# FUNCTIONAL VALIDATION TESTS
# =============================================================================


def test_current_top_story_content_validation(hackernews_api, top_story_id):
    """Test that current top story has reasonable field values, title, and author."""
    story = hackernews_api.get_item(top_story_id)

    # Verify reasonable field values
    assert story["id"] == top_story_id
    assert story["type"] == "story"
    assert len(story["by"]) > 0, "Author (by) should not be empty"
    assert story["time"] > 0, "Time should be positive Unix timestamp"
    assert len(story["title"]) > 0, "Title should not be empty"
    assert story["score"] >= 0, "Score should be non-negative"
    assert story["descendants"] >= 0, "Descendants count should be non-negative"

    # Title quality checks
    title = story["title"]
    assert len(title) >= 3, "Title should be at least 3 characters"
    assert len(title) <= 300, "Title should not be excessively long"
    assert title.strip() == title, "Title should not have leading/trailing whitespace"
    assert not title.isupper(), "Title should not be all uppercase (likely spam)"

    # Author validation
    author = story["by"]
    assert len(author) >= 1, "Author should not be empty"
    assert len(author) <= 50, "Author should not be excessively long"
    assert (
        author.strip() == author
    ), "Author should not have leading/trailing whitespace"


def test_current_top_story_timestamp_reasonable(hackernews_api, top_story_id):
    """Test that current top story has a reasonable timestamp."""
    import time

    story = hackernews_api.get_item(top_story_id)
    story_time = story["time"]
    current_time = int(time.time())

    # Timestamp should be within reasonable bounds
    # Stories shouldn't be from before HackerNews existed (2007) or in the future
    hackernews_launch = 1167609600  # Approximate timestamp for 2007

    assert (
        story_time >= hackernews_launch
    ), "Story timestamp too old (before HackerNews)"
    assert (
        story_time <= current_time + 3600
    ), "Story timestamp in future (allowing 1 hour skew)"


# =============================================================================
# NEGATIVE TESTS
# =============================================================================


def test_get_non_existent_story_response_code(hackernews_api):
    """Test response code when requesting non-existent story ID."""
    non_existent_id = 999999999

    with pytest.raises(ValueError, match=f"Item with ID {non_existent_id} not found"):
        hackernews_api.get_item(non_existent_id)

    # Verify response code is still 200 (API returns null for non-existent items)
    # Perhaps this should be a 404 in a real API, but HackerNews returns 200
    status_code = hackernews_api.get_status_code()
    assert status_code == 200


def test_get_invalid_story_id_validation(hackernews_api):
    """Test validation error when requesting invalid story ID."""
    invalid_id = -1
    with pytest.raises(
        ValueError, match=f"Invalid item_id: {invalid_id}. Must be a positive integer."
    ):
        hackernews_api.get_item(invalid_id)


def test_get_zero_story_id(hackernews_api):
    """Test that story ID 0 is treated as non-existent (not invalid)."""
    with pytest.raises(ValueError, match="Item with ID 0 not found"):
        hackernews_api.get_item(0)


def test_get_non_existent_story_response_content(hackernews_api):
    """Test response content when requesting non-existent story ID."""
    non_existent_id = 999999999

    with pytest.raises(ValueError, match=f"Item with ID {non_existent_id} not found"):
        hackernews_api.get_item(non_existent_id)

    # Verify raw response content is null
    raw_response = hackernews_api.get_response_text()
    assert raw_response == "null"
