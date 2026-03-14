import pytest

from src.clients import BaseWarehouseClient, USWarehouseClient


def make_order():
    """
    Example order from Shopify GraphQL Admin API
    """
    return {
        "id": "order-1",
        "lineItems": {
            "edges": [
                {"node": {"sku": "SKU-1", "quantity": 2}},
                {"node": {"sku": "SKU-2", "quantity": 1}},
            ]
        },
    }


def test_build_payload():
    """
    Test that orders are translated into payloads correctly
    """
    order = make_order()
    client = BaseWarehouseClient()

    payload = client._build_payload(order)

    assert payload["order_id"] == "order-1"
    assert len(payload["items"]) == 2
    assert payload["items"][0]["sku"] == "SKU-1"


def test_send_order_raises_when_no_endpoint():
    """
    Test that send_order raises NotImplementedError when ENDPOINT is not defined.
    """
    client = BaseWarehouseClient()
    with pytest.raises(NotImplementedError):
        client.send_order({"id": "x"})


def test_send_order_success_and_failure(monkeypatch):
    """
    Test that send_order correctly handles both successful and failed requests.
    """
    posted = {}

    def fake_post_success(url, json=None):
        posted["url"] = url
        posted["json"] = json

        class R:
            status_code = 200

            text = "ok"

        return R()

    def fake_post_fail(url, json=None):
        class R:
            status_code = 500

            text = "err"

        return R()

    # patch requests.post used by BaseWarehouseClient implementation
    monkeypatch.setattr(
        "src.clients.base_warehouse_client.requests.post", fake_post_success
    )

    client = USWarehouseClient()
    order = make_order()

    ok = client.send_order(order)
    assert ok is True
    assert posted["url"] == client.ENDPOINT

    # now fail
    monkeypatch.setattr(
        "src.clients.base_warehouse_client.requests.post", fake_post_fail
    )
    ok2 = client.send_order(order)
    assert ok2 is False
