# Job Skill Gap Agent

A personal tool I built for my own job search. It turns AI job posts into a structured database, finds which skills the market asks for most, and compares them with what I have actually studied and built, using my own notes. It runs entirely locally with Ollama.

## How it works

```
job post URL -> Fetch MCP server -> page as markdown
             -> LLM + Pydantic schema -> validated JobPost
             -> SQLite (jobs + skills)
                  -> top skills (SQL)
                  -> search_vault per skill (my notes, through my own MCP server)
                  -> LLM rates each skill -> skill gap report
```

The same pieces are used in two ways:

- **Workflow** (`save`, `report`): the steps are always the same, so plain code runs them.
- **Agent** (any other question): the LLM chooses from 6 tools and loops until it can answer.

| Tool | Source |
| --- | --- |
| `fetch` | Official Fetch MCP server |
| `search_vault`, `read_note`, `list_notes` | My second-brain MCP server (Obsidian notes + RAG) |
| `list_saved_jobs`, `top_skills` | Local Python functions over SQLite |

## Stack

Python 3.12 · LangChain `create_agent` / LangGraph · MCP (`langchain-mcp-adapters`) · Ollama (`qwen3.5:9b`, `nomic-embed-text`) · Pydantic structured outputs · SQLite · Chroma

## Running it

This is built around my personal setup: `report` and the chat depend on my second-brain MCP server, which searches my private Obsidian notes and isn't part of this repo. Running those parts yourself would need your own MCP server with a `search_vault` tool, set in `SECOND_BRAIN` in `mcp_servers.py`.

Saving job posts with `track.py` works on its own:

```
pip install -r requirements.txt
ollama pull qwen3.5:9b
python track.py
```

The database is created in `data/` on the first run.

## Usage

```
python agent.py
```

| Command | What it does |
| --- | --- |
| `save <url> [<url> ...]` | Fetch, extract and save job posts |
| `report` | Skill gap report across all saved posts |
| anything else | Ask the agent, e.g. `which skills are most requested, and do my notes cover them?` |
| `quit` | Exit |

`python track.py` saves the URLs listed in the file, and `python report.py` prints the report.

## Project layout

| File | Purpose |
| --- | --- |
| `schemas.py` | Pydantic schemas the LLM fills in: `JobPost`, `SkillRating` |
| `extract.py` | `extract(schema, instruction, text)`: text to validated object |
| `db.py` | SQLite tables and queries |
| `mcp_servers.py` | MCP server configuration and `fetch_page` |
| `track.py` | Pipeline: already saved? -> fetch -> extract -> save |
| `report.py` | Top skills and skill ratings |
| `agent.py` | Agent, command routing and chat loop |
| `samples/` | Example job posts for testing |

## Design decisions

- **Code for fixed steps, an agent for open questions.** Saving a post never needs an LLM to decide what to do next.
- **Exact work belongs in tools.** The agent miscounted skills across posts until counting moved to a SQL tool.
- **The schema goes in the prompt.** With Ollama's constrained decoding the model doesn't see `Field` descriptions, so the JSON schema is included in the prompt.
- **Required but nullable fields.** With `default=None` the model skipped keys entirely. Enums have an escape value (`unknown`, `other`), so it is never forced to guess.
- **Ratings are grounded in note metadata.** Search results include each note's type and status, and a rubric decides the rating, so a plan to learn something doesn't count as knowing it.

## Known limitations

- Skill ratings aren't fully reliable: a small local model sometimes justifies a rating with claims that aren't in the cited note, and borderline ratings can change between runs.

Next steps: evals on hand-labelled posts to measure extraction and rating accuracy, then use them to improve retrieval.
