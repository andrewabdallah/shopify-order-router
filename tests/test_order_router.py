from unittest.mock import Mock

from src.services import OrderRouter


def test_extract_skus_and_route_to_eu():
    """
    Test that SKUs are correctly extracted and routed to the EU warehouse.
    """
    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    order = {
        "id": "ord-1",
        "lineItems": {"edges": [{"node": {"sku": "EU-123"}}, {"node": {"sku": "X-1"}}]},
        "customer": {"email": "a@b.com"},
    }

    router.route_order(order)

    assert eu_client.send_order.call_count == 1
    sent_payload = eu_client.send_order.call_args[0][0]
    assert sent_payload["order_id"] == "ord-1"
    assert "EU-123" in sent_payload["skus"]


def test_route_to_us():
    """
    Test that SKUs are correctly extracted and routed to the US warehouse.
    """
    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    order = {"id": "ord-2", "lineItems": {"edges": [{"node": {"sku": "US-1"}}]}}

    router.route_order(order)

    assert us_client.send_order.call_count == 1
    sent_payload = us_client.send_order.call_args[0][0]
    assert sent_payload["order_id"] == "ord-2"
    assert sent_payload["skus"] == ["US-1"]


def test_mixed_routes_go_to_eu():
    """
    Test that mixed SKUs are correctly routed to the EU warehouse.
    """
    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    order = {
        "id": "ord-3",
        "lineItems": {"edges": [{"node": {"sku": "EU-1"}}, {"node": {"sku": "US-1"}}]},
    }

    router.route_order(order)

    assert eu_client.send_order.call_count == 1
    assert us_client.send_order.call_count == 0


def test_no_skus_does_not_route():
    """
    Test that orders with no SKUs do not get routed.
    """
    eu_client = Mock()
    us_client = Mock()

    router = OrderRouter({"EU_WAREHOUSE": eu_client, "US_WAREHOUSE": us_client})

    order = {"id": "ord-4", "lineItems": {"edges": []}}

    router.route_order(order)

    assert eu_client.send_order.call_count == 0
    assert us_client.send_order.call_count == 0


def test_missing_client_results_in_no_send():
    """
    Test that orders are not sent if the required client is missing.
    """
    eu_client = Mock()

    # only EU client provided but router will request US for this order
    router = OrderRouter({"EU_WAREHOUSE": eu_client})

    order = {"id": "ord-5", "lineItems": {"edges": [{"node": {"sku": "US-1"}}]}}

    router.route_order(order)

    # EU client should not have been called
    assert eu_client.send_order.call_count == 0
