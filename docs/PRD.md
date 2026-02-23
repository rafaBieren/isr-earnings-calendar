# Product Requirements Document (PRD)

## Phase
Phase 1: Repository spine and baseline documentation.

## Goal
Build an automated calendar generator that scrapes earnings event data from the Maya website and publishes it as an ICS feed.

## Target Users
Israeli investors who want earnings events in their calendar clients.

## Must-Haves
1. Scraping Maya earnings data.
2. Deduplication using security ID as the identity key.
3. ICS generation from normalized event data.

## Non-Goals
1. User authentication or user account management.
2. Scraping Telegram channels or groups.
