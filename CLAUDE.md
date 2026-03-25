# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BookJukBookJuk (책국책국)** — "A moment to get closer to books." A mobile web app combining social book discovery, AI-powered recommendations, and an intelligent reading assistant named **Paige**.

The core design document is `ai/paigee/docs/Paigee_agent_flow_docs.md` — read it before working on Paige.

## Rules

- **Never read `.env` files.** If `.env` values need to be set, describe what value to use and let the user update the file directly.

## Commands

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev       # Dev server at http://localhost:3000
npm run build     # Output to dist/
npm run preview   # Preview production build
```

### Backend AI (Python)
```bash
cd ai
pip install -r requirements.txt

# Taste analysis
python main.py --random
python main.py 9788937460470 9788936434120
python main.py --compare   # K-means vs DBSCAN

# Book Q&A chat
python book_chat_main.py --isbn 9788937460470
python book_chat_main.py --title "데미안" --author "헤르만 헤세"

# Hybrid recommender
python hybrid_recommender_main.py --user-isbn 9788937460470 9788936434120
python hybrid_recommender_main.py --interactive
python hybrid_recommender_main.py --load-dir ./saved_pipeline
```

### Required Environment Variables (see `ai/.env.example`)
- `OPENAI_API_KEY` — Required by all AI modules
- `LIBRARY_API_KEY` — 정보나루 Korean Library API (taste analysis, recommender)
- `ALADIN_API_KEY` — Aladin TTB book metadata API (book chat)
- `NEO4J_URI/USER/PASSWORD` — Optional; falls back to NetworkX in-memory KG
- `PINECONE_API_KEY/PINECONE_INDEX_NAME` — Optional; falls back to numpy in-memory vectors

## Architecture

### Frontend (`frontend/src/`)
React SPA with React Router. Pages: Home, Library, MyPage, BookDetail, BookChat, Search, Login. `MyChat.jsx` is the Paige chatbot on MyPage; `BookChat.jsx` is the book-specific Q&A page. Uses Leaflet for bookstore maps.

### AI Backend (`ai/`)
Three independent Python modules, each runnable standalone:

1. **Taste Analysis** (`taste_analysis/`, entry: `main.py`) — Fetches books from 정보나루, embeds keywords via OpenAI, clusters with K-means or DBSCAN, then generates an LLM prose analysis of reading preferences.

2. **Book Chat** (`book_chat/`, entry: `book_chat_main.py`) — Hybrid retrieval QA for a specific book. Pipeline: `data_collector` → `graph_builder` (KG) + `vector_store` (embeddings) → `retriever` (graph + vector blend) → `chat_engine` (LLM with relevance guard).

3. **Hybrid Recommender** (`hybrid_recommender/`, entry: `hybrid_recommender_main.py`) — 4-phase pipeline:
   - Phase 1 (`phase1_kg/`): LLM entity extraction → KG build (NetworkX or Neo4j) → noise filter
   - Phase 2 (`phase2_model/`): OpenAI embeddings + RippleNet GNN, cold-start handling, Pinecone or numpy storage
   - Phase 3 (`phase3_scoring/`): User profile tracking, hybrid score = α·Graph + (1-α)·Vector with time decay
   - Phase 4 (`phase4_xai/`): MMR diversity, ε-greedy exploration, LLM-generated explanations

### Paige Agent (`ai/paigee/`) — In Development
Design complete; implementation pending. Key concepts:

- **Channels:** MyPage chatbot (primary), Book Detail Q&A button, Bookstore channel (future)
- **Shared core:** All channels route through the same `Paige Core Orchestrator` — only `Channel Adapter` differs
- **Intents:** `state_change`, `book_qna_collect`, `review_assist`, `review_nudge`, `book_recommend`, `smalltalk`
- **State model:** `LIST → READING → RATED_ONLY → REVIEW_POSTED`
- **Key principle:** Paige *proposes* reviews/comments; it never auto-posts. Final submission is always user-triggered.
- **DB:** SQLite — tables: `users`, `books`, `book_user_states`, `ratings`, `comments`, `comment_suggestions`, `conversation_sessions`, `conversation_events`
- **Trigger priority** (MyPage): chat context ready (score 100) > rated without comment (60–80) > store followup (60) > recommend window (40) > default greeting (10)
