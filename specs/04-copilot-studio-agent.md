# Spec: Copilot Studio Agent

## Goal
Build a Microsoft Copilot Studio agent connected to the Power BI semantic
model (`olist_ecommerce_model`) so a user can ask natural-language questions
about the business and get answers grounded in the actual gold-layer data.
This satisfies the "conversational agent over your data" checkbox.

## Step type
**Manual/GUI step.** Copilot Studio has no Claude-Code-drivable interface —
Claude/Claude Code can draft the agent's name, description, and sample
grounding questions as plain text, but the human must configure the actual
agent and connector in the Copilot Studio web UI.

---

## AGENT SETUP

1. Go to https://copilotstudio.microsoft.com (sign in with the same
   Laurier/Waterloo account used for Power BI).
2. Create a new agent:
   - **Name**: `Olist Analytics Assistant`
   - **Description**: "Answers questions about Olist e-commerce performance —
     revenue, orders, delivery, sellers, and customer segments — grounded in
     the live Power BI semantic model."
3. Connect the Power BI data source:
   - In the agent's knowledge/data sources section, add the native
     **Power BI** connector.
   - Select the `olist_ecommerce_model` semantic model (the one built in
     `specs/03-powerbi-model.md`, living in "My workspace").
   - Confirm all 4 gold tables and 9 DAX measures are visible to the agent
     once connected.

---

## SAMPLE GROUNDING QUESTIONS

These are the test questions used to validate the agent actually answers
correctly from the model, and also serve as the demo script for the
application/portfolio write-up. Each should resolve using only the existing
DAX measures/tables — no new measures needed.

1. "What was our total revenue?"
   → should resolve via `[Total Revenue]`
2. "Which state generated the most revenue?"
   → should resolve via `daily_sales_by_region` grouped by `customer_state`
3. "What is our on-time delivery rate?"
   → should resolve via `[On-Time Delivery Rate]`
4. "Who are our top 5 sellers by revenue?"
   → should resolve via `seller_performance` sorted by `[Total Seller Revenue]`
5. "How many high-value customers do we have?"
   → should resolve via `customer_rfm` filtered to `rfm_segment = "High"`,
     counted
6. "What's the average order value?"
   → should resolve via `[Avg Order Value]`
7. "How does seller review score relate to revenue?"
   → open-ended/exploratory question, used to demo the agent handling a
     less structured ask against `seller_performance`

## Acceptance
- Agent responds correctly (matching the numbers already verified in the
  Power BI report) to at least questions 1–6 above.
- Question 7 doesn't need a "correct" answer — just needs to demonstrate the
  agent can reason over the connected data conversationally, not just
  regurgitate single numbers.

## Manual vs. Claude Code
Entirely manual — Copilot Studio agent creation, Power BI connector setup,
and testing all happen in the Copilot Studio web UI. Claude Code's only
contribution is having drafted this list of grounding questions.

## Next spec after this
`specs/05-rag-assistant.md` — the Claude API + vector store RAG chatbot
over the data dictionary/business glossary. This is a fully Claude-Code-
drivable step (no GUI dependency), independent of Copilot Studio, and can
be built in parallel or afterward.
