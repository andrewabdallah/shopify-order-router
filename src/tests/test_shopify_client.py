from clients import ShopifyClient


def test_get_orders_pagination(monkeypatch):
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
