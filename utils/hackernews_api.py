"""Hacker News API client."""

from typing import Any

from requests import Response

from utils.requester import Requester


class HackerNewsAPI:
    """Client for Hacker News API.

    API Documentation: https://github.com/HackerNews/API
    """

    def __init__(self, config: object):
        """Initialize HackerNews API client.

        Args:
            config: Configuration object with base_url, timeout, max_retries attributes
        """
        self.requester = Requester(
            base_url=config.base_url,
            timeout=getattr(config, "timeout", 10.0),
            max_retries=getattr(config, "max_retries", 3),
        )
        self.last_response = None

    def get_top_stories(self, limit: int | None = None) -> list[int]:
        """Get top story IDs from Hacker News.

        Args:
            limit: Optional limit for number of stories to return.
                   If not specified, returns all top stories (up to 500).

        Returns:
            List of story IDs

        Raises:
            requests.HTTPError: If the API request fails
            ValueError: If response is not valid JSON
        """
        response = self.requester.request("GET", "topstories.json")
        self.last_response = response
        response.raise_for_status()

        story_ids = response.json()

        if limit and limit > 0:
            return story_ids[:limit]

        return story_ids

    def get_item(self, item_id: int) -> dict[str, Any]:
        """Get item details by ID.

        Items can be stories, comments, jobs, polls, or poll options.

        Args:
            item_id: The item's unique ID

        Returns:
            Dictionary containing item details with fields:
            - id: The item's unique id
            - type: The type of item (story, comment, job, poll, pollopt)
            - by: Username of the item's author (optional)
            - time: Creation time (Unix timestamp)
            - text: Comment/story/poll text in HTML (optional)
            - url: URL of the story (optional)
            - title: Title of the story/poll/job (optional)
            - score: Story/poll score (optional)
            - descendants: Total comment count for stories/polls (optional)
            - kids: List of comment IDs (optional)
            - parent: Parent comment/story ID (optional)
            - parts: List of poll option IDs (optional)
            - poll: Poll ID for poll options (optional)

        Raises:
            requests.HTTPError: If the API request fails
            ValueError: If response is not valid JSON or item_id is invalid
        """
        if not isinstance(item_id, int) or item_id < 0:
            raise ValueError(f"Invalid item_id: {item_id}. Must be a positive integer.")

        response = self.requester.request("GET", f"item/{item_id}.json")
        self.last_response = response
        response.raise_for_status()

        item_data = response.json()

        # API returns null for non-existent items
        if item_data is None:
            raise ValueError(f"Item with ID {item_id} not found")

        return item_data

    def get_top_stories_with_details(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top stories with their full details.

        This is a convenience method that combines get_top_stories and get_item.

        Args:
            limit: Number of stories to fetch (default: 10)

        Returns:
            List of story dictionaries with full details

        Raises:
            requests.HTTPError: If any API request fails
            ValueError: If response is not valid JSON
        """
        story_ids = self.get_top_stories(limit=limit)
        stories = []

        for story_id in story_ids:
            try:
                story = self.get_item(story_id)
                stories.append(story)
            except (ValueError, Exception) as e:
                # Log error but continue with other stories
                print(f"Failed to fetch story {story_id}: {e}")
                continue

        return stories

    def get_last_response(self) -> Response | None:
        """Get the last HTTP response object.

        Returns:
            Last Response object or None if no requests have been made
        """
        return self.last_response

    def get_status_code(self) -> int | None:
        """Get the HTTP status code of the last response.

        Returns:
            HTTP status code or None if no requests have been made
        """
        return self.last_response.status_code if self.last_response else None

    def get_headers(self) -> dict[str, str] | None:
        """Get the headers of the last response.

        Returns:
            Response headers as dictionary or None if no requests have been made
        """
        return dict(self.last_response.headers) if self.last_response else None

    def get_response_text(self) -> str | None:
        """Get the raw text of the last response.

        Returns:
            Raw response text or None if no requests have been made
        """
        return self.last_response.text if self.last_response else None

    def close(self) -> None:
        """Close the underlying requester session."""
        if self.requester:
            self.requester.close()
