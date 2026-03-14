from unittest.mock import Mock

from src.clients.shopify_client import ShopifyClient
from src.services import OrderRouter


def test_shopify_to_router_integration(monkeypatch):
    """End-to-end flow: ShopifyClient -> OrderRouter -> warehouse clients (mocked)."""

    responses = [
        {
            "data": {
                "orders": {
                    "edges": [
                        {
                            "node": {
                                "id": "1",
                                "lineItems": {"edges": [{"node": {"sku": "EU-1"}}]},
                            }
                        },
                        {
                            "node": {
                                "id": "2",
                                "lineItems": {"edges": [{"node": {"sku": "US-1"}}]},
                            }
                        },
                    ],
                    "pageInfo": {"hasNextPage": True, "endCursor": "c1"},
                }
            }
        },
        {
            "data": {
                "orders": {
                    "edges": [
                        {
                            "node": {
                                "id": "3",
                                "lineItems": {"edges": [{"node": {"sku": "EU-2"}}]},
                            }
                        }
                    ],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        },
    ]

    it = iter(responses)

    def _fake_execute(self, query, variables=None):
        return next(it)

    monkeypatch.setattr(
        "src.clients.shopify_client.ShopifyClient._execute_query", _fake_execute
    )

    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    client = ShopifyClient("https://example", "token")
    for order in client.get_orders():
        router.route_order(order)

    # two EU orders (ids 1 and 3), one US order (id 2)
    assert eu_client.send_order.call_count == 2
    assert us_client.send_order.call_count == 1
