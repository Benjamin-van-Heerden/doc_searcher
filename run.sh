#!/bin/bash
cd "$(dirname "${BASH_SOURCE[0]}")"
source .venv/bin/activate
crawl4ai-setup
uv run main.py
