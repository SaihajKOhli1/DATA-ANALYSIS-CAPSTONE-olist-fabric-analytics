# Spec: Silver & Gold Layer ETL

## Goal
Transform the 9 raw bronze Delta tables (`olist_ecommerce.bronze.*`) into cleaned,
deduplicated silver tables, then aggregate those into gold-layer fact tables that
Power BI will consume directly via the SQL endpoint / Databricks connector.

## Step type
Claude Code step — fully code-driven, run in the Databricks notebook
(`02_silver_gold_etl`, PySpark/pandas logic same as bronze notebook).

---

## SILVER LAYER

Target schema: `olist_ecommerce.silver`

### 1. `silver.orders`
- **Source**: `bronze.orders`
- **Dedup key**: `order_id` (drop exact duplicate rows if any)
- **Transform**: cast all timestamp-looking columns (`order_purchase_timestamp`,
  `order_approved_at`, `order_delivered_carrier_date`,
  `order_delivered_customer_date`, `order_estimated_delivery_date`) to proper
  timestamp type.
- **Acceptance**: row count == bronze row count (no dupes expected here), no
  nulls in `order_id`.

### 2. `silver.order_items`
- **Source**: `bronze.order_items`
- **Dedup key**: (`order_id`, `order_item_id`)
- **Transform**: cast `price`, `freight_value` to decimal/double; cast
  `shipping_limit_date` to timestamp.
- **Acceptance**: row count == bronze row count.

### 3. `silver.order_payments`
- **Source**: `bronze.order_payments`
- **Dedup key**: (`order_id`, `payment_sequential`)
- **Transform**: cast `payment_value` to decimal/double.
- **Acceptance**: row count == bronze row count.

### 4. `silver.order_reviews`
- **Source**: `bronze.order_reviews`
- **Known issue**: some `order_id`s have multiple review rows (duplicate or
  updated reviews).
- **Dedup rule (CONFIRMED — Option A)**: for each `order_id`, keep only the row
  with the **latest `review_creation_date`** (if tie, latest
  `review_answer_timestamp`).
- **Transform**: cast `review_creation_date`, `review_answer_timestamp` to
  timestamp; cast `review_score` to integer.
- **Acceptance**: exactly one row per `order_id` in the output.

### 5. `silver.customers`
- **Source**: `bronze.customers`
- **Dedup key**: `customer_id`
- **Transform**: none beyond basic type casts (zip prefix as string, not int —
  Brazilian zip prefixes can have leading zeros).
- **Acceptance**: row count == bronze row count.

### 6. `silver.sellers`
- **Source**: `bronze.sellers`
- **Dedup key**: `seller_id`
- **Transform**: zip prefix as string (same leading-zero reasoning as customers).
- **Acceptance**: row count == bronze row count.

### 7. `silver.products`
- **Source**: `bronze.products` joined with `bronze.category_translation`
- **Dedup key**: `product_id`
- **Transform**: join in `product_category_name_english` via
  `product_category_name`; drop the Portuguese-only column after join; cast
  numeric dimension/weight columns to double.
- **Acceptance**: row count == bronze `products` row count (left join, no
  fan-out).

### 8. `silver.geolocation`
- **Source**: `bronze.geolocation`
- **Known issue**: many rows per `geolocation_zip_code_prefix` (multiple
  individual addresses logged under the same prefix).
- **Dedup rule (CONFIRMED)**: collapse to **one row per
  `geolocation_zip_code_prefix`**, taking the **average lat/lng** across all
  rows for that prefix, and the most frequent (`mode`) city/state values for
  that prefix.
- **Acceptance**: row count == count of distinct `geolocation_zip_code_prefix`
  values in bronze.

---

## GOLD LAYER

Target schema: `olist_ecommerce.gold`

### 1. `gold.daily_sales_by_region`
- **Grain**: one row per (`order_date`, `customer_state`)
- **Source**: `silver.orders` joined to `silver.order_items` (for revenue) and
  `silver.customers` (for state)
- **Measures**:
  - `order_date` = date part of `order_purchase_timestamp`
  - `revenue` = sum of `price + freight_value` across order_items for that
    date+state
  - `order_count` = count of distinct `order_id`
- **Acceptance**: no duplicate (date, state) rows; revenue sums reconcile to
  total silver order_items revenue.

### 2. `gold.seller_performance`
- **Grain**: one row per `seller_id`
- **Source**: `silver.order_items` (revenue, order count) joined to
  `silver.order_reviews` via `order_id` (avg review score) and `silver.sellers`
  (seller metadata)
- **Measures**:
  - `total_revenue` = sum of `price + freight_value` across all items sold by
    that seller
  - `order_count` = count of distinct `order_id`
  - `avg_review_score` = average `review_score` across reviews tied to that
    seller's orders
- **Acceptance**: one row per `seller_id`, no nulls in `total_revenue`.

### 3. `gold.delivery_sla`
- **Grain**: one row per `order_id`
- **Source**: `silver.orders`
- **Measures**:
  - `estimated_delivery_date` = `order_estimated_delivery_date`
  - `actual_delivery_date` = `order_delivered_customer_date`
  - `delivery_delta_days` = actual - estimated (negative = early, positive =
    late)
  - `on_time_flag` = 1 if `delivery_delta_days` <= 0 else 0
- **Note**: exclude orders where `order_delivered_customer_date` is null (not
  yet delivered / cancelled) — filter these out or flag separately, do not
  count them as late.
- **Acceptance**: one row per delivered `order_id`; no negative-infinity or
  nonsense deltas from null dates.

---

## Manual vs. Claude Code
This entire spec is a **Claude Code step** — no manual UI work required beyond
running the notebook cells in Databricks.

## Next spec after this
`specs/03-powerbi-model.md` — once gold tables exist, connect Power BI via the
Databricks connector and build DAX measures / report pages on top of these
three gold tables.
