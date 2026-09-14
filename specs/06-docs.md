# Spec: Docs & Publishing

## Goal
Produce the repo's public-facing documentation: a root `README.md` that
explains the project, its architecture, the two infrastructure pivots, and
how to run the RAG assistant locally. This is the deliverable a reviewer
(or hiring manager) actually reads first.

## Step type
**Claude Code step for content generation.** Writing the README itself is
fully Claude-Code-drivable — it's markdown authored from the project's
existing specs, ETL script, and verified business summary, no GUI
involved. The *repo itself being the deliverable* is what makes this spec
worth calling out separately from specs 01–05, not the mechanics of
producing it.

Architecture diagram screenshots (if a Databricks/Power BI screenshot is
later added alongside the Mermaid diagram) would be a manual step — take a
screenshot in-browser, save to `docs/`. Not required for this pass; the
Mermaid diagram in the README is sufficient and renders natively on
GitHub.

---

## Status of specs 01–05

All five prior specs are complete and pushed to `main`:

1. **Bronze ingestion** — 9 raw CSVs loaded into `olist_ecommerce.bronze`.
2. **Silver/gold ETL** (`specs/02-silver-gold-etl.md`) — silver dedup rules
   applied, 3 initial gold tables built.
3. **Power BI model** (`specs/03-powerbi-model.md`) — `gold.customer_rfm`
   added, 3-page report built manually in Power BI Desktop.
4. **Copilot Studio agent** (`specs/04-copilot-studio-agent.md`) —
   attempted, blocked by tenant licensing, formally abandoned in favor of
   folding its scope into the RAG assistant.
5. **RAG assistant** (`specs/05-rag-assistant.md`) — data dictionary,
   business summary, local TF-IDF vector store, and `rag/query.py` CLI, all
   built and live-tested.

### Part 4 (live grounding-question test) — completed successfully

All 9 grounding questions carried over from the abandoned Copilot Studio
spec were run against the real Claude API via `rag/query.py` and returned
correct, well-grounded answers:

1. "What was our total revenue?" → correct total, order count, AOV
2. "Which state generated the most revenue?" → correct (SP)
3. "What is our on-time delivery rate?" → correct (93.23%)
4. "Who are our top 5 sellers by revenue?" → correct table, matched
   `business_summary.md`
5. "How many high-value customers do we have?" → correct (21,695)
6. "What's the average order value?" → correct (R$160.58)
7. "How does seller review score relate to revenue?" → demonstrated
   reasoning over retrieved context (no strong positive correlation in the
   top 10, correctly explained via the order-level review attribution
   caveat), not a single canned number
8. "What does the recency_days column mean?" → correct data-dictionary
   definition
9. "Why might avg_review_score look off for some sellers?" → correctly
   surfaced both data-quality caveats (order-level review attribution and
   the ~1,069 malformed `review_score` rows)

No environment or credential blockers were hit in the end: the local
Python environment (`anthropic`, `scikit-learn`, `databricks-sql-connector`
installed via `pip3`) worked without architecture-mismatch issues, and
`ANTHROPIC_API_KEY` was supplied via the shell environment for the test
run. The script does not read `.env` files or persist the key anywhere —
it must be exported by whoever runs it, each session.

One unrelated environment note from earlier in this phase: an attempt to
query the Databricks gold tables directly via
`databricks-sql-connector` (to source live figures for
`business_summary.md` instead of manually exported CSVs) hit a TLS
certificate verification failure in the local sandbox (a MITM proxy
presents a self-signed cert that Python's `certifi` bundle doesn't trust,
though the system `curl`/keychain does). This was worked around by using
manually exported CSVs from the Databricks notebook instead — see
`rag/business_summary.md` for the resulting figures. This is a sandbox
networking quirk, not a project or code defect.

---

## README requirements

Root `README.md` must cover:

1. **Project overview** — portfolio project demonstrating a full modern
   data stack (lakehouse ETL, BI reporting, RAG assistant), built to
   satisfy a job application's tech stack checklist.
2. **Architecture diagram** — Mermaid diagram (renders natively on GitHub)
   showing bronze → silver → gold → Power BI → RAG assistant.
3. **Tech stack**, explicit and honest about both pivots:
   - Microsoft Fabric → Databricks Free Edition (tenant workspace-creation
     restriction)
   - Copilot Studio agent → folded into the Claude RAG assistant (tenant
     licensing restriction — "user license not found")

   Framed as adapting to real infrastructure constraints encountered
   mid-project, not as failures.
4. **What's built** — ETL row counts and key data-quality decisions
   (`order_reviews` dedup rule, `geolocation` collapse, the ~1,069
   malformed `review_score` rows), the Power BI report's 3 pages and DAX
   measures, and the RAG assistant's two-part scope.
5. **Repo structure** explanation.
6. **How to run the RAG assistant locally** — required env var
   (`ANTHROPIC_API_KEY`), install steps, example invocation.
7. **Example business questions** the project can answer, as a short
   narrative (revenue by region, delivery SLA performance, top sellers).

## Manual vs. Claude Code
Entirely Claude Code — the README is generated content, not a GUI step.
Optional future addition (manual): dashboard/report screenshots dropped
into `docs/` and linked from the README.

## Next spec after this
None currently planned — this closes out the project's documentation
phase. Future specs would cover any additional features (e.g. a hosted
version of the RAG assistant, CI for the ETL, etc.) if pursued.
