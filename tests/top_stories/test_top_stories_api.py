"""Tests for HackerNews Top Stories API endpoint."""

import pytest
from pydantic import BaseModel, Field, ValidationError


class TopStoriesResponse(BaseModel):
    """Schema for top stories API response - list of story IDs."""

    stories: list[int] = Field(..., min_length=1, max_length=500)


# =============================================================================
# API CONTRACT VALIDATION TESTS
# =============================================================================


def test_get_top_stories_response_code_200(hackernews_api):
    """Test that top stories endpoint returns HTTP 200."""
    hackernews_api.get_top_stories()

    status_code = hackernews_api.get_status_code()
    assert status_code == 200


def test_get_top_stories_response_headers(hackernews_api):
    """Test that top stories endpoint returns appropriate headers."""
    hackernews_api.get_top_stories()

    headers = hackernews_api.get_headers()

    # Verify essential headers exist
    assert headers is not None
    assert "Content-Type" in headers

    # Content type should be JSON
    content_type = headers["Content-Type"].lower()
    assert "application/json" in content_type


def test_get_top_stories_response_schema_validation(hackernews_api):
    """Test that top stories response matches expected schema using Pydantic."""
    stories = hackernews_api.get_top_stories()

    # Validate response structure using Pydantic model
    try:
        validated_response = TopStoriesResponse(stories=stories)
        assert len(validated_response.stories) > 0
        assert len(validated_response.stories) <= 500  # API returns up to 500 stories
    except ValidationError as e:
        pytest.fail(f"Response schema validation failed: {e}")


def test_get_top_stories_returns_list_of_integers(hackernews_api):
    """Test that top stories endpoint returns a list of story IDs as integers."""
    stories = hackernews_api.get_top_stories()

    assert isinstance(stories, list)
    assert len(stories) > 0
    assert all(isinstance(story_id, int) for story_id in stories)
    assert all(story_id > 0 for story_id in stories)


# =============================================================================
# FUNCTIONAL VALIDATION TESTS
# =============================================================================


@pytest.mark.parametrize("limit", [1, 5, 10, 25, 100])
def test_get_top_stories_with_limit_parameter(hackernews_api, limit):
    """Test top stories endpoint with various limit values."""
    stories = hackernews_api.get_top_stories(limit=limit)

    assert isinstance(stories, list)
    assert len(stories) == limit
    assert all(isinstance(story_id, int) for story_id in stories)
    assert all(story_id > 0 for story_id in stories)


def test_get_top_stories_without_limit_returns_all(hackernews_api):
    """Test that calling without limit returns all available stories."""
    all_stories = hackernews_api.get_top_stories()
    limited_stories = hackernews_api.get_top_stories(limit=10)

    # All stories should contain more items than limited
    assert len(all_stories) > len(limited_stories)

    # Limited stories should be the first N items from all stories
    assert limited_stories == all_stories[:10]


def test_get_top_stories_story_ids_are_unique(hackernews_api):
    """Test that returned story IDs are unique."""
    stories = hackernews_api.get_top_stories(limit=50)

    # Convert to set and compare lengths to check uniqueness
    unique_stories = set(stories)
    assert len(unique_stories) == len(stories)


def test_get_top_stories_response_time_reasonable(hackernews_api):
    """Test that top stories endpoint responds in reasonable time."""
    import time

    start_time = time.perf_counter()
    hackernews_api.get_top_stories(limit=10)
    elapsed_time = time.perf_counter() - start_time

    # API should respond within 1 second for small limits
    assert elapsed_time < 1.0


def test_get_top_stories_consecutive_calls_consistency(hackernews_api):
    """Test that consecutive calls return consistent top stories."""
    # Get top 5 stories twice
    first_call = hackernews_api.get_top_stories(limit=5)
    second_call = hackernews_api.get_top_stories(limit=5)

    # Stories should be consistent (allowing for some variation due to real-time updates)
    # At least the first story should be the same in most cases
    assert len(first_call) == len(second_call) == 5

    # Check that there's significant overlap (at least 80% of stories are the same)
    common_stories = set(first_call) & set(second_call)
    overlap_percentage = len(common_stories) / len(first_call)
    assert overlap_percentage >= 0.8


# =============================================================================
# NEGATIVE TESTS
# =============================================================================


@pytest.mark.parametrize("limit", [0, -1, -10])
def test_get_top_stories_with_invalid_limits(hackernews_api, limit):
    """Test top stories endpoint behavior with invalid limit values."""
    # With invalid limits, should return empty list or all stories
    stories = hackernews_api.get_top_stories(limit=limit)

    # Verify response code is still 200 (API handles invalid limits gracefully)
    # That is probably a defect, should return 400 Bad Request
    status_code = hackernews_api.get_status_code()
    assert status_code == 200

    # API should handle gracefully - either return empty list or ignore invalid limit
    assert isinstance(stories, list)


def test_get_top_stories_large_limit_handled_gracefully(hackernews_api):
    """Test that requesting more stories than available is handled gracefully."""
    # Request more than the maximum (500) stories
    stories = hackernews_api.get_top_stories(limit=1000)

    # Should return at most 500 stories (API maximum)
    # That is probably a defect, should return 400 Bad Request
    # It is like silently ignoring the limit, which is not ideal
    assert isinstance(stories, list)
    assert len(stories) <= 500
