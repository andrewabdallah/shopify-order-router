# Shopify GraphQL Order Routing Middleware

This project implements a Python-based middleware integration that retrieves orders from Shopify using the **Shopify Admin GraphQL API** and routes them to the appropriate warehouse system based on SKU rules.

The solution simulates a real-world integration workflow where order data is retrieved from an e-commerce platform, business rules are applied, and orders are forwarded to downstream warehouse systems.

---

# Overview

The integration performs the following steps:

1. Authenticate with Shopify using the Admin API access token.
2. Retrieve orders via the Shopify **GraphQL Admin API**.
3. Extract relevant order and SKU data.
4. Apply SKU-based routing rules.
5. Send or simulate sending the order payload to the correct warehouse endpoint.

The project is designed with a modular architecture to clearly separate **API communication**, **business logic**, and **application orchestration**.

---

# Architecture

The system follows a simple middleware pattern:

Shopify API → ShopifyClient → OrderRouter → WarehouseClient → Warehouse API

### Components

| Component                                 | Responsibility                                    |
| ----------------------------------------- | --------------------------------------------------|
| **ShopifyClient**                         | Communicates with the Shopify GraphQL API         |
| **OrderRouter**                           | Applies routing business logic                    |
| **BaseWarehouseClient**                   | Abstract class for warehouse clients              |
| **EUWarehouseClient / USWarehouseClient** | Warehouse-specific implementations to send orders |
| **main.py**                               | Application entry point                           |
| **tests/**                                | Unit tests with mocked responses                  |

This structure keeps API integrations independent from business logic and allows the system to scale if additional warehouse systems are added.

---

# Business Routing Logic

Orders are routed to warehouses based on SKU prefixes.

Routing rules:

1. If **any SKU starts with `EU-`** → route the order to the **EU warehouse**
2. Else if **any SKU starts with `US-`** → route the order to the **US warehouse**

Edge cases handled:

| Case                 | Behavior                             |
| -------------------- | ------------------------------------ |
| EU SKUs only         | Routed to EU warehouse               |
| US SKUs only         | Routed to US warehouse               |
| Mixed EU and US SKUs | Routed to EU warehouse (EU priority) |
| Unknown SKU prefixes | Order is skipped and logged          |

---

# Shopify GraphQL API

Orders are retrieved using the Shopify Admin GraphQL API endpoint:

/admin/api/2026-01/graphql.json

Example GraphQL query used in the integration:

```graphql
query ($cursor: String) {
  orders(first: 10, after: $cursor) {
    edges {
      node {
        id
        name
        customer {
          email
        }
        lineItems(first: 10) {
          edges {
            node {
              sku
              quantity
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

The implementation supports **cursor-based pagination** using `pageInfo.hasNextPage` and `endCursor`.

---

# Features

### GraphQL API Integration

Uses Shopify’s modern **Admin GraphQL API** instead of the deprecated REST Admin API.

### Pagination Support

Orders are retrieved using Shopify’s cursor-based pagination.

### Retry Logic

API calls implement retry logic with exponential backoff using the **tenacity** library.

### Logging

Structured logging is used to track:

* order routing decisions
* API requests
* errors and failures

### Clean Architecture

The codebase separates:

* API communication
* business logic
* payload transformation

### Unit Testing

Unit tests use **mocking** to simulate Shopify responses and warehouse integrations.

---

# Project Structure

```
src/
  clients/
    shopify_client.py
    base_warehouse_client.py
    eu_warehouse_client.py
    us_warehouse_client.py

  services/
    order_router.py

  utils/
    logger.py

  main.py

tests/
  test_order_router.py
  test_shopify_client.py

requirements.txt
README.md
```

---

# Setup Instructions

Clone the repository:

```
git clone https://github.com/andrewabdallah/shopify-order-router.git
cd shopify-order-router
```

Create a virtual environment:

```
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# Environment Variables

The following environment variables are required:

```
SHOPIFY_SHOP_URL=https://store.myshopify.com
SHOPIFY_ACCESS_TOKEN=access-token
SHOPIFY_API_VERSION=2026-01
```

These values can be configured using environment variables or a `.env` file.

---

# Running the Application

Run the integration workflow:

```
python -m src.main
```

The application will:

1. Retrieve orders from Shopify
2. Evaluate SKU routing rules
3. Send orders to the appropriate warehouse client

---

# Running Tests

Unit tests simulate Shopify responses using mocks.

Run tests with:

```
pytest
```

---

# Assumptions

The following assumptions were made for this exercise:

* Shopify orders may contain mixed SKU prefixes.
* When both EU and US SKUs exist, **EU takes precedence** according to the routing rules.
* Orders without valid SKU prefixes are logged and skipped.
* Warehouse endpoints are simulated for demonstration purposes.

---

# Possible Improvements

Potential enhancements for a production environment:

* support for additional warehouse systems
* configuration-based routing rules
* asynchronous API requests
* monitoring and metrics
* containerization with Docker
* message queue integration for large order volumes

---

# Author

Andrew Abdallah
