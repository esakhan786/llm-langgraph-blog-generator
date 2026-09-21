# AI Blog Generator

A Streamlit-based AI blog generation app powered by LangGraph and Google Gemini.

## Features
- Generate blog topic and audience-based articles
- Research + draft generation workflow
- Human-in-the-loop approval and revision
- Final blog output with download support
- Generate multiple blog topics sequentially
- Clean dark portfolio-style UI

## Project Structure
- `app.py` - Streamlit frontend
- `graph.py` - LangGraph workflow
- `state.py` - State schema
- `agent.py` - LLM agents and prompt logic
- `blog_gen.ipynb` - notebook version for testing
- `.env` - API keys and environment variables

## Tech Stack
- Python
- Streamlit
- LangChain
- LangGraph
- Google Gemini API
- Python-dotenv

## Setup
1. Create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate