# Spec: Copilot Studio Agent (ABANDONED — see below)

## Status: Abandoned, pivoted to RAG assistant

Attempted to connect a Copilot Studio agent to the Power BI semantic model
(`olist_ecommerce_model`). Blocked by a Microsoft tenant/licensing
restriction on the Laurier/Waterloo account used for this project:

- The Power BI knowledge-source connector did not appear under either the
  "Featured" or "Advanced" tabs when adding knowledge to the agent.
- Attempting to fall back to file-based knowledge (uploading CSV exports of
  the gold tables) failed with: "You don't have permission to create
  agents" / "You don't have permission to upload files to this agent" —
  both errors citing "User license not found."

This mirrors the earlier Microsoft Fabric workspace-creation block hit at
the start of this project — both are tenant-level licensing restrictions
outside the project's control, not implementation errors.

## Decision
Rather than lose the "conversational agent grounded in your data"
deliverable entirely, its scope is folded into
`specs/05-rag-assistant.md`: the Claude API + vector store RAG assistant
originally scoped only for the data dictionary/business glossary will also
be able to answer the business-metrics questions originally intended for
the Copilot Studio agent (see the "SAMPLE GROUNDING QUESTIONS" list below,
now carried over into the RAG spec).

This keeps the project fully deliverable using tools within this project's
control (Claude API, a vector store, and the already-verified gold-layer
data), rather than depending on Microsoft tenant licensing that can't be
resolved without contacting Laurier/Waterloo IT — which is outside the
scope of a portfolio project on a deadline.

## Original grounding questions (carried over to RAG assistant spec)
1. "What was our total revenue?"
2. "Which state generated the most revenue?"
3. "What is our on-time delivery rate?"
4. "Who are our top 5 sellers by revenue?"
5. "How many high-value customers do we have?"
6. "What's the average order value?"
7. "How does seller review score relate to revenue?"

## Manual vs. Claude Code
N/A — abandoned before any Claude-Code-relevant work was done (agent setup
and knowledge-source configuration are both GUI-only steps in Copilot
Studio).

## Next spec after this
`specs/05-rag-assistant.md` — now scoped to cover both the original data
dictionary Q&A and the business-metrics questions above.
