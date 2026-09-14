# Olist E-Commerce Analytics Project

## What this is
A portfolio project building an end-to-end analytics stack on the Olist Brazilian 
e-commerce dataset, to demonstrate a full modern data stack: lakehouse ETL, BI reporting, 
a conversational agent, and a RAG assistant. Built to satisfy a job application's tech 
stack checklist.

## Tech stack
- **Data platform**: Databricks Free Edition + Unity Catalog (originally planned as 
  Microsoft Fabric, switched due to tenant/account restrictions — see specs/00-platform-switch.md 
  if it exists)
- **Storage**: Delta Lake tables, medallion architecture (bronze/silver/gold), organized 
  as three schemas under the `olist_ecommerce` catalog
- **ETL**: Python/PySpark, run in Databricks notebooks
- **BI**: Power BI, connected to gold-layer tables via the Databricks connector
- **Conversational agent**: Microsoft Copilot Studio, connected to the Power BI semantic model
- **RAG assistant**: Claude API + vector store, answering questions about the data 
  dictionary/business glossary
- **Docs/publishing**: GitHub repo with architecture diagram, README, dashboard screenshots

## Architecture
Raw CSVs → Unity Catalog Volume (bronze/raw_files)
→ bronze Delta tables (raw, typed, 1:1 with source CSVs)
→ silver Delta tables (deduplicated, cleaned, validated)
→ gold Delta tables (aggregated fact tables)
→ Power BI (via Databricks connector) → Copilot Studio agent
Data dictionary (separate) → RAG chatbot (Claude API)


## Current state
- Catalog `olist_ecommerce` created in Databricks (Unity Catalog, Standard type, 
  default storage)
- Schemas created: `bronze`, `silver`, `gold`
- Bronze layer complete: all 9 raw CSVs uploaded to 
  `/Volumes/olist_ecommerce/bronze/raw_files` and loaded into bronze Delta tables 
  via notebook `01_bronze_ingestion`
- Silver/gold spec drafted: `specs/02-silver-gold-etl.md`
- Silver/gold ETL script being generated: `etl/02_silver_gold_etl.py` (Databricks 
  notebook-format, to be pasted into a Databricks notebook and run there — Claude Code 
  cannot execute against the Databricks workspace directly)

## Working conventions
- **Specs first**: any nontrivial transform or aggregation gets a spec in `specs/` 
  before code is written. Specs define grain, dedup rules, and acceptance criteria.
- **Claude Code vs. manual split**: ETL (Python/PySpark) and the RAG assistant are 
  Claude-Code-drivable end to end. Power BI report building and Copilot Studio agent 
  config are GUI-driven — Claude Code drafts DAX/M/topic text, but the human does the 
  actual clicking in-browser.
- Databricks notebook code should be written in Databricks' notebook export format 
  (`# COMMAND ----------` as cell dividers) so it can be pasted directly into a 
  Databricks notebook.
- Gold-layer tables are the direct source for Power BI — schema changes there should 
  be treated as breaking changes to downstream reports.

## Repo layout
/specs/ one markdown spec per phase, written before code
/data/raw/ local copies of Olist CSVs (source for bronze upload)
/etl/ PySpark/pandas scripts (bronze->silver, silver->gold)
/gold/ exported gold-layer outputs if needed locally
/powerbi/ DAX measures, Power Query M scripts, .pbix
/copilot-studio/ exported topics/config, sample grounding Q&A
/rag/ data dictionary docs, vector store build script, query script
/docs/ architecture diagram, README, screenshots
CLAUDE.md this file