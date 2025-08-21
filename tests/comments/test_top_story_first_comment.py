"""Tests for retrieving first comment of top story using Top Stories and Items APIs."""

import pytest
from pydantic import BaseModel, Field, ValidationError


class CommentItem(BaseModel):
    """Schema for a comment item from Items API."""

    id: int = Field(..., gt=0)
    type: str = Field(..., pattern="^comment$")
    by: str = Field(..., min_length=1)
    time: int = Field(..., gt=0)
    text: str = Field(..., min_length=1)
    parent: int = Field(..., gt=0)
    kids: list[int] | None = Field(default=None)


@pytest.fixture(scope="module")
def top_story_with_comments(hackernews_api):
    """Fixture that finds a top story that has comments.

    Args:
        hackernews_api: HackerNews API client fixture

    Returns:
        dict: Story item that has comments (kids field)
    """
    # Get top stories and find one with comments
    top_stories = hackernews_api.get_top_stories(limit=10)

    for story_id in top_stories:
        story = hackernews_api.get_item(story_id)

        # Look for a story that has comments
        if story.get("kids") and len(story["kids"]) > 0:
            return story

    # If no stories with comments found in top 10, fail the test
    pytest.fail("No top stories with comments found in the first 10 stories")


@pytest.fixture(scope="module")
def first_comment_id(top_story_with_comments):
    """Fixture that returns the first comment ID from a top story.

    Args:
        top_story_with_comments: Story with comments fixture

    Returns:
        int: The ID of the first comment
    """
    kids = top_story_with_comments.get("kids", [])
    assert len(kids) > 0, "Story should have at least one comment"

    first_comment_id = kids[0]
    assert isinstance(first_comment_id, int), "Comment ID should be an integer"
    assert first_comment_id > 0, "Comment ID should be positive"

    return first_comment_id


# =============================================================================
# API CONTRACT VALIDATION TESTS
# =============================================================================


def test_first_comment_response_code_200(hackernews_api, first_comment_id):
    """Test that retrieving first comment returns HTTP 200."""
    hackernews_api.get_item(first_comment_id)

    status_code = hackernews_api.get_status_code()
    assert status_code == 200


def test_first_comment_response_headers(hackernews_api, first_comment_id):
    """Test that first comment endpoint returns appropriate headers."""
    hackernews_api.get_item(first_comment_id)

    headers = hackernews_api.get_headers()

    # Verify essential headers exist
    assert headers is not None
    assert "Content-Type" in headers

    # Content type should be JSON
    content_type = headers["Content-Type"].lower()
    assert "application/json" in content_type


def test_first_comment_schema_validation(hackernews_api, first_comment_id):
    """Test that first comment response matches expected schema using Pydantic."""
    comment = hackernews_api.get_item(first_comment_id)

    # Validate comment structure using Pydantic model
    try:
        validated_comment = CommentItem(**comment)
        assert validated_comment.id == first_comment_id
        assert validated_comment.type == "comment"
        assert len(validated_comment.text) > 0
        assert validated_comment.parent > 0
    except ValidationError as e:
        pytest.fail(f"Comment schema validation failed: {e}")


# =============================================================================
# FUNCTIONAL VALIDATION TESTS
# =============================================================================


def test_first_comment_content_validation(
    hackernews_api, first_comment_id, top_story_with_comments
):
    """Test that first comment has required fields, correct types, reasonable values, text quality, and valid author."""
    comment = hackernews_api.get_item(first_comment_id)

    # Required fields for a comment
    required_fields = ["id", "type", "by", "time", "text", "parent"]
    for field in required_fields:
        assert field in comment, f"Required field '{field}' missing from comment"
        assert comment[field] is not None, f"Required field '{field}' is None"

    # Verify field types
    assert isinstance(comment["id"], int)
    assert isinstance(comment["type"], str)
    assert isinstance(comment["by"], str)
    assert isinstance(comment["time"], int)
    assert isinstance(comment["text"], str)
    assert isinstance(comment["parent"], int)

    # Optional kids field type check (if present)
    if "kids" in comment and comment["kids"] is not None:
        assert isinstance(comment["kids"], list)
        assert all(isinstance(kid_id, int) for kid_id in comment["kids"])

    # Verify reasonable field values
    assert comment["id"] == first_comment_id
    assert comment["type"] == "comment"
    assert len(comment["by"]) > 0, "Author (by) should not be empty"
    assert comment["time"] > 0, "Time should be positive Unix timestamp"
    assert len(comment["text"]) > 0, "Comment text should not be empty"
    assert (
        comment["parent"] == top_story_with_comments["id"]
    ), "Parent should match the story ID"

    # Text quality checks
    text = comment["text"]
    assert len(text) >= 1, "Comment text should not be empty"
    assert len(text) <= 10000, "Comment text should not be excessively long"
    # Note: Comments might have HTML tags, so we don't strip HTML here

    # Author validation
    author = comment["by"]
    assert len(author) >= 1, "Author should not be empty"
    assert len(author) <= 50, "Author should not be excessively long"
    assert (
        author.strip() == author
    ), "Author should not have leading/trailing whitespace"


def test_first_comment_timestamp_reasonable(
    hackernews_api, first_comment_id, top_story_with_comments
):
    """Test that first comment has a reasonable timestamp."""
    import time

    comment = hackernews_api.get_item(first_comment_id)
    comment_time = comment["time"]
    story_time = top_story_with_comments["time"]
    current_time = int(time.time())

    # Comment timestamp should be after story timestamp
    assert comment_time >= story_time, "Comment should be posted after the story"

    # Comment shouldn't be in the future
    assert (
        comment_time <= current_time + 3600
    ), "Comment timestamp in future (allowing 1 hour skew)"


def test_first_comment_parent_relationship(
    hackernews_api, first_comment_id, top_story_with_comments
):
    """Test that first comment correctly references its parent story."""
    comment = hackernews_api.get_item(first_comment_id)

    # Parent should be the story ID
    assert comment["parent"] == top_story_with_comments["id"]

    # Verify the story actually lists this comment as a child
    story_kids = top_story_with_comments.get("kids", [])
    assert first_comment_id in story_kids, "Story should list this comment in its kids"


def test_comment_chain_integrity(hackernews_api, top_story_with_comments):
    """Test the integrity of the comment chain from story to first comment."""
    story = top_story_with_comments

    # Verify story has comments
    assert "kids" in story
    assert len(story["kids"]) > 0

    # Get the first comment
    _first_comment_id = story["kids"][0]
    comment = hackernews_api.get_item(_first_comment_id)

    # Verify the chain: Story -> Comment
    assert comment["parent"] == story["id"]
    assert comment["type"] == "comment"
    assert story["type"] == "story"
