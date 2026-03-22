# what-should-we-eat 🍽️

> An AI-orchestrated system for deciding what we eat.

## Architecture

This project follows a 3-layer architecture (see `AGENTS.md` for full details):

| Layer | Location | Purpose |
|---|---|---|
| **Directive** | `directives/` | SOPs — what to do and why |
| **Orchestration** | AI agent | Decision-making and routing |
| **Execution** | `execution/` | Deterministic Python scripts |

## Setup

```bash
# 1. Copy env template and fill in your keys
cp .env.template .env

# 2. Install Python dependencies
pip install -r requirements.txt   # (create this as needed)
```

## Directory Structure

```
.
├── AGENTS.md           # AI operating instructions
├── directives/         # SOPs for each repeatable task
├── execution/          # Python scripts (Layer 3)
├── .tmp/               # Intermediate files (gitignored, regenerated freely)
├── .env                # Secrets (gitignored)
└── .env.template       # Safe-to-commit template
```
