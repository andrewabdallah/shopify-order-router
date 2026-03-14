from unittest.mock import Mock, patch

import requests
from pytest import raises
from tenacity import RetryError

from src.clients import ShopifyClient


def test_get_orders_pagination(monkeypatch):
    """
    Test that the ShopifyClient correctly handles paginated order responses.
    """
    client = ShopifyClient("https://example.myshopify.com", "token")

    responses = [
        {
            "data": {
                "orders": {
                    "edges": [{"node": {"id": "1", "name": "Order1"}}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "abc"},
                }
            }
        },
        {
            "data": {
                "orders": {
                    "edges": [{"node": {"id": "2", "name": "Order2"}}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
    ]

    it = iter(responses)

    def _fake_execute(self, query, variables=None):
        return next(it)

    monkeypatch.setattr(ShopifyClient, "_execute_query", _fake_execute)

    orders = list(client.get_orders())

    assert len(orders) == 2
    assert orders[0]["id"] == "1"
    assert orders[1]["id"] == "2"


@patch("requests.post")
def test_retry_on_shopify_failure(mock_post):
    """Test that the ShopifyClient retries on transient failures."""

    # First response: raise HTTPError on raise_for_status()
    first_resp = Mock()
    first_resp.raise_for_status.side_effect = requests.HTTPError("Server Error")

    # Second response: successful JSON payload
    second_resp = Mock()
    second_resp.raise_for_status.return_value = None
    second_resp.json.return_value = {
        "data": {"orders": {"edges": [], "pageInfo": {"hasNextPage": False}}}
    }

    mock_post.side_effect = [first_resp, second_resp]

    client = ShopifyClient("https://example.myshopify.com", "token")
    orders = list(client.get_orders())

    # Should have retried once and returned empty list
    assert mock_post.call_count == 2
    assert orders == []


@patch("src.clients.shopify_client.requests.post")
def test_retry_stops_after_max_attempts(mock_post):
    """Ensure the tenacity retry on _execute_query stops after configured attempts."""

    # Simulate a response whose raise_for_status always raises
    bad_resp = Mock()
    bad_resp.raise_for_status.side_effect = requests.HTTPError("Server Error")
    mock_post.return_value = bad_resp

    client = ShopifyClient("https://example", "token")

    with raises(RetryError):
        client._execute_query("query")

    # stop_after_attempt(3) -> function should have been called 3 times
    assert mock_post.call_count == 3


@patch("src.clients.shopify_client.requests.post")
def test_execute_query_raises_on_invalid_json(mock_post):
    """If the HTTP response can't be parsed as JSON, the retry wrapper will raise RetryError."""

    resp = Mock()
    resp.raise_for_status.return_value = None
    resp.json.side_effect = ValueError("Invalid JSON")

    mock_post.return_value = resp

    client = ShopifyClient("https://example", "token")

    with raises(RetryError):
        # forcing evaluation of the generator triggers the underlying _execute_query
        list(client.get_orders())
