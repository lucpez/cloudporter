# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Project Overview

CloudPorter is a CLI tool that translates a provider-agnostic CloudPorter Manifest (YAML) into deployable OpenTofu templates for different cloud providers.

## Architecture

## Language and runtime

- Python 3.14, managed with `uv`
- Install dependencies: `uv sync`
- Run the cloudporter CLI: `uv run cloudporter`

## Quality tools

| Tool | Purpose |
|------|---------|
| `ruff` | Linter and formatter |
| `mypy` | Static type checking (strict mode) |
| `pytest` | Tests (≥80% coverage required) |
| `pre-commit` | Runs ruff + mypy before every commit and pytest -m "not slow" on push|

Key commands:
- `uv run ruff check . && uv run ruff format .`
- `uv run mypy src`
- `uv run pytest`
- `uv run pytest -m "not slow"` — skip slow tests

## Conventions

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) — `type(scope): description`
- **Branches:** `feat/<number>-<description>` — one branch per issue
- **PRs:** merged to `main` only after CI passes; `main` is protected
