# Spec: Claude RAG Assistant

## Goal
Build a RAG (retrieval-augmented generation) chatbot using the Claude API
and a vector store that can answer two kinds of questions:
1. **Data dictionary questions** — "what does this column mean," "why might
   this metric look off" — grounded in a written data dictionary/business
   glossary.
2. **Business-metrics questions** — the questions originally scoped for the
   (abandoned, see `specs/04-copilot-studio-agent.md`) Copilot Studio
   agent, e.g. "what was our total revenue," "who are our top sellers" —
   grounded in exported summaries of the gold-layer tables.

This is a fully Claude-Code-drivable step: no GUI dependency, no external
licensing risk (unlike Fabric and Copilot Studio, both blocked by tenant
restrictions earlier in this project).

## Step type
**Claude Code step.** Everything here — writing the data dictionary docs,
exporting gold-table summaries, building the vector store, writing the
retrieval script, and wiring up the Claude API — is code Claude Code can
write and run directly.

---

## PART 1: Data dictionary / business glossary

Write `rag/data_dictionary.md` — a markdown document covering, for each
gold table:
- Table name and one-line purpose
- Grain (one row per what)
- Each column: name, meaning, unit/type
- Known data-quality caveats (carried over from `specs/02-silver-gold-etl.md`
  and the conversation that built it):
  - `order_reviews` dedup: ~1,069 rows had malformed `review_score` values
    from CSV parsing issues (embedded special characters in free-text
    review comments), handled via `try_cast` → nulled, excluded from
    averages
  - `order_reviews` row count (99,743) is slightly higher than total orders
    (99,441) due to a small number of corrupted `order_id` values in the
    raw data that don't match real orders
  - `seller_performance.avg_review_score`: since some Olist orders contain
    items from multiple sellers, a single review can be counted toward more
    than one seller's average score — an inherent quirk of the dataset,
    not a bug
  - `geolocation` collapsed from ~1,000,163 raw rows to 19,015 (one row per
    zip-code prefix, using average lat/lng and the mode city/state)

Cover all 4 gold tables: `daily_sales_by_region`, `seller_performance`,
`delivery_sla`, `customer_rfm`.

## PART 2: Business-metrics summary export

Export current summary figures from the gold tables (small, human-readable
— not raw row dumps) into `rag/business_summary.md`:
- Total revenue, total orders, avg order value (from `daily_sales_by_region`)
- On-time delivery rate, avg delivery delta (from `delivery_sla`)
- Top 10 sellers by revenue with avg review score (from `seller_performance`)
- Revenue by state, ranked (from `daily_sales_by_region`)
- Customer segment breakdown: count and avg monetary value per
  `rfm_segment` (from `customer_rfm`)

These are the same figures already verified in the Power BI report — this
file is a static text snapshot of them for the RAG assistant to retrieve
from, not a live connection.

## PART 3: Vector store + retrieval script

- Chunk `rag/data_dictionary.md` and `rag/business_summary.md` into
  retrievable sections (e.g. one chunk per table/section).
- Embed and store chunks in a simple local vector store (e.g. a lightweight
  file-based store — no need for a hosted vector DB for this scale of
  content).
- Write `rag/query.py`: takes a user question, retrieves the most relevant
  chunks, and sends them as context to the Claude API along with the
  question, returning a grounded answer.

## PART 4: Test against the original grounding questions

Run these through the finished script (carried over from the abandoned
Copilot Studio spec) and confirm reasonable, correct answers:
1. "What was our total revenue?"
2. "Which state generated the most revenue?"
3. "What is our on-time delivery rate?"
4. "Who are our top 5 sellers by revenue?"
5. "How many high-value customers do we have?"
6. "What's the average order value?"
7. "How does seller review score relate to revenue?"
8. "What does the recency_days column mean?" (data dictionary question)
9. "Why might avg_review_score look off for some sellers?" (data quality
   caveat question)

## Acceptance
- Questions 1–6 and 8–9 resolve to answers matching the numbers/facts
  already verified in the Power BI report and the ETL conversation.
- Question 7 and similar open-ended questions demonstrate the assistant
  reasoning over retrieved context rather than just pattern-matching a
  single number.
- Script runs locally via `python rag/query.py "<question>"` or similar
  simple CLI interface — no deployment required for this to count as
  "built."

## Implementation notes (post-build)

- Chunking/retrieval implemented as a local TF-IDF vector store
  (`rag/build_index.py`, using scikit-learn's `TfidfVectorizer` +
  cosine similarity) rather than a hosted embeddings API — appropriate
  given the corpus is two short markdown files (~12 chunks total), and it
  avoids requiring a second API key (e.g. Voyage AI) beyond
  `ANTHROPIC_API_KEY`.
- `rag/business_summary.md` figures were sourced from CSV exports of the
  gold tables run directly in the Databricks notebook (rather than a live
  connection from this environment) — see `specs/06-docs.md` for the
  reason (a local sandbox TLS/certificate issue blocked direct
  `databricks-sql-connector` access).
- All 9 grounding questions in Part 4 were run live against the real
  Claude API and returned correct, well-grounded answers — see
  `specs/06-docs.md` for the full results.

## Manual vs. Claude Code
Entirely Claude Code — no manual/GUI steps in this spec.

## Next spec after this
`specs/06-docs.md` — README, architecture diagram, screenshots, and the
GitHub publish. Should mention the Fabric→Databricks and Copilot
Studio→RAG pivots as part of the project's real story, not hide them.
