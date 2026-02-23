# Technical Specification

## Stack
- Python
- FastAPI for backend/API
- SQLite for storage

## Core Components
1. Scraper module for Maya earnings data ingestion.
2. SQLite persistence layer for normalized records and deduplication state.
3. ICS generation module exposed through FastAPI.

## Scheduling Model
The scraper runs on a schedule via cron or an internal background task, depending on deployment/runtime constraints.

## Scope Note
This document defines implementation direction only; no application code is included in Phase 1.
