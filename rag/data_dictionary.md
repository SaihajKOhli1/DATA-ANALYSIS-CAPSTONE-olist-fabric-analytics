# Data Dictionary / Business Glossary

Covers the four gold-layer tables in `olist_ecommerce.gold`, the direct
source for Power BI and this RAG assistant. Each gold table is built from
the `olist_ecommerce.silver.*` tables per `specs/02-silver-gold-etl.md` and
`specs/03-powerbi-model.md`.

---

## `daily_sales_by_region`

**Purpose**: Daily revenue and order volume broken out by customer state.
Powers the executive KPI dashboard and the regional revenue view in Power BI.

**Grain**: one row per (`order_date`, `customer_state`).

**Columns**:
| Column | Meaning | Unit / Type |
|---|---|---|
| `order_date` | Date part of the order's purchase timestamp | date |
| `customer_state` | Brazilian state abbreviation of the customer who placed the order | string (2-letter code, e.g. `SP`) |
| `revenue` | Sum of `price + freight_value` across all order items purchased on that date by customers in that state | decimal (BRL) |
| `order_count` | Count of distinct orders on that date/state | integer |

**Data-quality caveats**: none specific to this table beyond the general
silver-layer dedup rules (see `silver.orders`, `silver.order_items` in
`specs/02-silver-gold-etl.md`).

---

## `seller_performance`

**Purpose**: Per-seller revenue, order volume, and average customer review
score. Powers the seller leaderboard/table in Power BI.

**Grain**: one row per `seller_id`.

**Columns**:
| Column | Meaning | Unit / Type |
|---|---|---|
| `seller_id` | Unique seller identifier | string |
| `total_revenue` | Sum of `price + freight_value` across all items sold by this seller | decimal (BRL) |
| `order_count` | Count of distinct orders containing at least one item from this seller | integer |
| `avg_review_score` | Average `review_score` (1–5) across reviews tied to orders that included this seller's items | decimal, 1.0–5.0 |
| `seller_zip_code_prefix`, `seller_city`, `seller_state` | Seller's registered location, carried through from `silver.sellers` | string |

**Data-quality caveats**:
- `avg_review_score` can be misleading for sellers who frequently co-appear
  on multi-seller orders: since some Olist orders contain items from
  multiple sellers, a single review (which is scored at the *order* level,
  not the item level) gets counted toward the average of every seller on
  that order. A seller who happens to often share orders with a
  poorly-reviewed co-seller will show a lower `avg_review_score` than their
  own individual performance might warrant. This is an inherent quirk of
  how Olist collects reviews, not a bug in the ETL.
- `avg_review_score` inherits the `order_reviews` dedup/parsing caveats
  described under `order_reviews` below (malformed scores nulled before
  averaging).

---

## `delivery_sla`

**Purpose**: Delivery timeliness per order — actual vs. estimated delivery
date. Powers the on-time delivery rate KPI and delivery delta analysis.

**Grain**: one row per delivered `order_id`. Orders that were never
delivered (`order_delivered_customer_date` is null — still in transit,
cancelled, etc.) are excluded entirely, not counted as late.

**Columns**:
| Column | Meaning | Unit / Type |
|---|---|---|
| `order_id` | Unique order identifier | string |
| `estimated_delivery_date` | Delivery date Olist quoted to the customer at time of purchase | date/timestamp |
| `actual_delivery_date` | Date the order was actually delivered to the customer | date/timestamp |
| `delivery_delta_days` | `actual_delivery_date - estimated_delivery_date`, in days. Negative = delivered early, positive = delivered late, 0 = delivered exactly on the estimated date | integer (days) |
| `on_time_flag` | 1 if `delivery_delta_days <= 0` (on time or early), else 0 | integer (0/1) |

**Data-quality caveats**: none beyond the exclusion of undelivered orders
noted above.

---

## `customer_rfm`

**Purpose**: Customer segmentation using Recency/Frequency/Monetary (RFM)
analysis. Powers the customer segmentation report page.

**Grain**: one row per `customer_unique_id` — note this is Olist's
cross-order customer identifier, distinct from `customer_id`, which Olist
assigns a new value to per order. Using `customer_unique_id` is what makes
this a true "one row per real customer" table instead of "one row per
order."

**Columns**:
| Column | Meaning | Unit / Type |
|---|---|---|
| `customer_unique_id` | Unique identifier for a real customer across all their orders | string |
| `recency_days` | Days between this customer's most recent order purchase timestamp and the latest order purchase timestamp in the entire dataset. In other words: "as of the last day we have data for, how many days had it been since this customer last ordered?" A smaller number means a more recently active customer. This is *not* days-since-today — the dataset has a fixed end date. | integer (days) |
| `frequency` | Count of distinct orders this customer has placed | integer |
| `monetary` | Sum of `price + freight_value` across all order items across all of this customer's orders | decimal (BRL) |
| `rfm_segment` | `High`, `Medium`, or `Low` — derived by scoring each of recency, frequency, and monetary into tertiles (`ntile(3)`, best tertile = highest score) and summing the three scores into a `combined_score`: `High` = combined_score <= 4, `Medium` = 5–6, `Low` = 7–9. This is a simple heuristic segmentation, not a formal statistical model. | string |

**Data-quality caveats**: none specific to this table.

---

## Cross-cutting data-quality notes (apply to multiple gold tables)

### `order_reviews` malformed `review_score` values
During the silver-layer build, ~1,069 rows in `order_reviews` had malformed
`review_score` values caused by CSV parsing issues — the raw
`review_comment_message` free-text field sometimes contained embedded
special characters (quotes, delimiters) that corrupted the adjacent
`review_score` column during ingestion. These rows were handled with
`try_cast` during typing: values that don't cleanly cast to integer are set
to null rather than guessed at, and null review scores are excluded from
all `avg_review_score` calculations (they don't count as zero or get
dropped from the table entirely — the row stays, just without a score
contributing to averages).

### `order_reviews` row count vs. order count
`order_reviews` has 99,743 rows after silver-layer dedup, slightly more
than the 99,441 total orders in `orders`. This is because a small number of
raw `order_id` values in the reviews CSV are corrupted and don't match any
real order — they don't get filtered out during the dedup step (dedup is
per `order_id`, and a corrupted ID is still a distinct "order_id" to dedup
against), so they persist as extra rows that don't join cleanly to
`orders`. This is a known raw-data quirk, not an ETL bug.

### `geolocation` collapse
The raw `geolocation` bronze table has ~1,000,163 rows (one row per
individually logged address). The silver layer collapses this to 19,015
rows — one row per distinct `geolocation_zip_code_prefix` — by averaging
`geolocation_lat`/`geolocation_lng` across all rows sharing a prefix, and
taking the mode (most frequent) `geolocation_city`/`geolocation_state` for
that prefix. This means `geolocation` values are an approximation at the
zip-prefix level, not exact per-address coordinates. (Note: none of the
four gold tables currently join against `geolocation` directly — this
caveat matters if it's added to a future gold table.)
