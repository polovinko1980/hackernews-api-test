"""HTTP Requester wrapper for API testing."""

from urllib.parse import urljoin

from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Requester:
    """Simple wrapper class for requests library."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
    ):
        """Initialize the Requester.

        Args:
            base_url: Base URL for all requests
            timeout: Default timeout in seconds
            headers: Default headers to include in all requests
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Backoff factor for retries
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = Session()

        # Setup retry strategy
        retry = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        if headers:
            self.session.headers.update(headers)

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from base URL and endpoint."""
        if self.base_url and not endpoint.startswith(("http://", "https://")):
            return urljoin(self.base_url, endpoint)
        return endpoint

    def request(self, method: str, endpoint: str, **kwargs) -> Response:
        """Make HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object
        """
        url = self._build_url(endpoint)
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, url, **kwargs)

    def close(self) -> None:
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
