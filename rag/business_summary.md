# Business Metrics Summary

Static snapshot of key figures from the `olist_ecommerce.gold` tables, as
verified in the Power BI report. This is not a live connection — if the
underlying data changes, this file needs to be regenerated.

---

## Overall Sales (from `daily_sales_by_region`)

- **Total revenue**: R$15,843,553.24
- **Total orders**: 98,666
- **Average order value**: R$160.58

---

## Delivery Performance (from `delivery_sla`)

- **On-time delivery rate**: 93.23% (orders delivered on or before the
  estimated delivery date)
- **Average delivery delta**: -11.88 days (on average, orders arrive about
  12 days *earlier* than the estimated delivery date — Olist appears to set
  conservative delivery estimates)

---

## Top 10 Sellers by Revenue (from `seller_performance`)

| Rank | Seller ID | Total Revenue | Avg Review Score |
|---|---|---|---|
| 1 | `4869f7a5dfa277a7dca6462dcf3b52b2` | R$249,640.70 | 4.13 |
| 2 | `7c67e1448b00f6e969d365cea6b010ab` | R$239,536.44 | 3.49 |
| 3 | `53243585a1d6dc2643021fd1853d8905` | R$235,856.68 | 4.13 |
| 4 | `4a3ca9315b744ce9f8e9374361493884` | R$235,539.96 | 3.83 |
| 5 | `fa1c13f2614d7b5c4749cbc52fecda94` | R$204,084.73 | 4.34 |
| 6 | `da8622b14eb17ae2831f4ac5b9dab84a` | R$185,192.32 | 4.18 |
| 7 | `7e93a43ef30c4f03f38b393420bc753a` | R$182,754.05 | 4.21 |
| 8 | `1025f0e2d44d7041d6cf58b6550e0bfa` | R$172,860.69 | 3.99 |
| 9 | `7a67c85e85bb2ce8582c35f2203ad736` | R$162,648.38 | 4.25 |
| 10 | `955fee9216a65b617aa5c0531780ce60` | R$160,602.68 | 4.16 |

Observation: among the top 10 sellers by revenue, review scores range from
3.49 to 4.34 — there is no strong positive correlation between revenue
rank and review score in this top slice. The #1 seller by revenue
(4.13) and #2 (3.49, the lowest score in the top 10) show that high sales
volume does not require a top-tier review score. This is consistent with
the `seller_performance` data-quality caveat in the data dictionary: review
scores are attributed at the order level and can be shared across sellers
on multi-seller orders, which dampens the signal between an individual
seller's actual service quality and their measured `avg_review_score`.

---

## Revenue by State, Ranked (from `daily_sales_by_region`)

| Rank | State | Revenue | Orders |
|---|---|---|---|
| 1 | SP | R$5,921,678.12 | 41,375 |
| 2 | RJ | R$2,129,681.98 | 12,762 |
| 3 | MG | R$1,856,161.49 | 11,544 |
| 4 | RS | R$885,826.76 | 5,432 |
| 5 | PR | R$800,935.44 | 4,998 |
| 6 | BA | R$611,506.67 | 3,358 |
| 7 | SC | R$610,213.60 | 3,612 |
| 8 | DF | R$353,229.44 | 2,125 |
| 9 | GO | R$347,706.93 | 2,007 |
| 10 | ES | R$324,801.91 | 2,025 |
| 11 | PE | R$322,237.69 | 1,648 |
| 12 | CE | R$275,606.30 | 1,327 |
| 13 | PA | R$217,647.11 | 970 |
| 14 | MT | R$186,168.96 | 903 |
| 15 | MA | R$151,171.99 | 740 |
| 16 | PB | R$140,987.81 | 532 |
| 17 | MS | R$135,956.67 | 709 |
| 18 | PI | R$108,132.28 | 493 |
| 19 | RN | R$101,895.08 | 482 |
| 20 | AL | R$96,229.40 | 411 |
| 21 | SE | R$73,032.32 | 345 |
| 22 | TO | R$61,354.42 | 279 |
| 23 | RO | R$57,558.02 | 247 |
| 24 | AM | R$27,835.73 | 147 |
| 25 | AC | R$19,669.70 | 81 |
| 26 | AP | R$16,262.80 | 68 |
| 27 | RR | R$10,064.62 | 46 |

São Paulo (SP) alone accounts for roughly 37% of total revenue, more than
the next two states (RJ, MG) combined.

---

## Customer Segments (from `customer_rfm`)

| Segment | Customer Count | % of Customers | Avg Monetary Value |
|---|---|---|---|
| High | 21,695 | 22.7% | R$236.52 |
| Medium | 31,691 | 33.2% | R$160.14 |
| Low | 42,034 | 44.1% | R$134.11 |

Total customers across all segments: 95,420. "High-value" customers (the
`High` `rfm_segment`) number 21,695, with an average monetary value of
R$236.52 — about 1.76x the average monetary value of `Low`-segment
customers.
