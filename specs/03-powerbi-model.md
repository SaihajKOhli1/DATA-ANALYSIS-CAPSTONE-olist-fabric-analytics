# Spec: Power BI Model & Report Pages

## Goal
Connect Power BI to the gold-layer Delta tables and build a 3-page report:
an executive KPI dashboard, a regional/seller performance breakdown, and a
customer segmentation (RFM) view. This is the primary deliverable Power BI
checkbox for the application.

## Step type
**Manual/GUI step.** Power BI Desktop (or Power BI service) has no
Claude-Code-drivable interface — Claude Code/Claude can draft DAX measure
text and Power Query M scripts as plain text, but the human must paste them
into Power BI's formula bar / Power Query editor and build the report pages
by hand.

---

## PRE-REQUISITE: new gold table needed

### `gold.customer_rfm`
- **Grain**: one row per `customer_unique_id` (not `customer_id` — Olist's
  `customers` table has a separate surrogate `customer_id` per order, but
  `customer_unique_id` identifies the actual repeat customer across orders)
- **Source**: `silver.orders` joined to `silver.customers` (for
  `customer_unique_id`) and `silver.order_items` (for monetary value)
- **Measures**:
  - `recency_days` = days between the customer's most recent
    `order_purchase_timestamp` and the max order date across the whole
    dataset (i.e. "days since last order, as of the last day we have data
    for")
  - `frequency` = count of distinct `order_id` for that customer
  - `monetary` = sum of `price + freight_value` across all of that
    customer's order_items
  - `rfm_segment` = simple tertile-based label (e.g. "High/Medium/Low" on
    each of recency, frequency, monetary — or a combined score); keep this
    simple, don't over-engineer a scoring model
- **Acceptance**: one row per `customer_unique_id`; no negative
  `recency_days`; `frequency` >= 1 for every row.
- **Step type**: Claude Code step — same pattern as the other gold tables,
  runs as a notebook cell in `02_silver_gold_etl` (or a new
  `03_customer_rfm` cell/notebook) in Databricks.

---

## POWER BI CONNECTION

1. Open Power BI Desktop (or Power BI service).
2. **Get Data** → search for **Databricks** → select the native Databricks
   connector.
3. Enter the Databricks workspace URL and HTTP path (found in Databricks:
   **Compute** → your SQL warehouse / serverless endpoint → **Connection
   details**).
4. Authenticate (personal access token or OAuth, whichever Databricks Free
   Edition supports for this connector).
5. Select all 4 gold tables: `daily_sales_by_region`, `seller_performance`,
   `delivery_sla`, `customer_rfm`.
6. Load in **Import** mode (not DirectQuery) — dataset is small, Import
   gives better report performance and full DAX support.

---

## DAX MEASURES (to create in Power BI's Modeling tab)

### From `daily_sales_by_region`
- `Total Revenue` = `SUM(daily_sales_by_region[revenue])`
- `Total Orders` = `SUM(daily_sales_by_region[order_count])`
- `Avg Order Value` = `DIVIDE([Total Revenue], [Total Orders])`

### From `delivery_sla`
- `On-Time Delivery Rate` =
  `DIVIDE(SUM(delivery_sla[on_time_flag]), COUNTROWS(delivery_sla))`
- `Avg Delivery Delta (Days)` = `AVERAGE(delivery_sla[delivery_delta_days])`

### From `seller_performance`
- `Total Seller Revenue` = `SUM(seller_performance[total_revenue])`
- `Avg Seller Review Score` = `AVERAGE(seller_performance[avg_review_score])`

### From `customer_rfm`
- `Customer Count` = `DISTINCTCOUNT(customer_rfm[customer_unique_id])`
- `Avg Customer Monetary Value` = `AVERAGE(customer_rfm[monetary])`

---

## REPORT PAGES

### Page 1: Executive KPI Dashboard
- Card visuals: `Total Revenue`, `Total Orders`, `Avg Order Value`,
  `On-Time Delivery Rate`
- Line chart: revenue over time (from `daily_sales_by_region`, date on
  x-axis)
- Slicer: date range, customer state

### Page 2: Regional & Seller Performance
- Map or bar chart: revenue by `customer_state` (from
  `daily_sales_by_region`)
- Table: top sellers by `total_revenue`, with `avg_review_score` column
  (from `seller_performance`)
- Bar chart: `Avg Delivery Delta (Days)` by state, if state is joinable in
  (optional stretch — only if time permits)

### Page 3: Customer Segmentation (RFM)
- Scatter plot: recency (x) vs. frequency (y), bubble size = monetary
  (from `customer_rfm`)
- Table: customers grouped by `rfm_segment`, with count and avg monetary
  value per segment
- Card: `Customer Count`, `Avg Customer Monetary Value`

---

## Manual vs. Claude Code
- **Claude Code**: builds `gold.customer_rfm` (PySpark, run in Databricks)
- **Manual**: everything else in this spec — Power BI connection, DAX
  measure entry, report page layout/visuals

## Next spec after this
`specs/04-copilot-studio-agent.md` — once the Power BI semantic model
exists, connect a Copilot Studio agent to it via the native Power BI
connector.
