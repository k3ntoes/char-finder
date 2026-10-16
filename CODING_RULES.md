# CODING_RULES.md — AI Development Guidelines for Capo Finder

This document defines the strict engineering standards, architectural decisions, and coding rules for AI agents developing and maintaining **Capo Finder**.

---

## 1. 🛡️ Mandatory Skill Rule (`/ponytail`)
Before writing, refactoring, or adding any code, the agent MUST review and strictly follow the `/ponytail` skill principles:
- **YAGNI (You Aren't Gonna Need It)**: Do not implement speculative features or unused boilerplate.
- **Standard Library First**: Leverage Python's built-in modules (`math`, `statistics`, `collections`, `sqlite3`, `asyncio`, `json`) before reaching for external packages.
- **Native Platform Features**: Prefer native HTML5/CSS3 and FastAPI features over heavy third-party packages.
- **Simpler/Shortest Working Code**: Write clean, readable, straightforward code.
- **Zero Premature Abstractions**: Avoid over-engineering classes, factories, or abstract base classes until clearly required by duplication.

---

## 2. ⚡ Environment & Package Management (`uv`)
- **Package Manager**: Always use `uv` for dependency management and running scripts.
  - Run app: `uv run uvicorn main:app --reload`
  - Add dependency: `uv add fastapi uvicorn aiohttp apscheduler jinja2`
- **Minimal Dependencies**: Keep dependencies strictly limited to:
  - `fastapi`
  - `uvicorn[standard]`
  - `jinja2`
  - `aiohttp`
  - `apscheduler`
- **Virtual Environment**: `uv` automatically manages the virtual environment (`.venv`). Never manually configure raw virtualenv paths unless necessary.

---

## 3. 🧮 Data & Math Processing
- **Zero External Scientific Libraries**: Absolutely NO `pandas`, NO `numpy`, NO `scikit-learn`.
- **Pure Python Standard Library**: Use `math`, `statistics`, and `collections` for all data processing, OLS regressions, and Empirical Bayes shrinkage calculations.
  - Ensures blazing speed (~2.5ms latency) and minimal memory footprint (~1MB RAM).

---

## 4. 🗄️ SQLite Best Practices
- **Parameterized Queries**: Always use parameterized queries (`?`) for SQL statements to prevent SQL injection.
- **Context Managers**: Ensure database connections are properly handled via context managers (`with sqlite3.connect(...) as conn:`).
- **Transactions**: Use transactions (`conn.commit()`) for batch inserts/updates (e.g., price history logging).
- **Lamport Storage**: Store market prices in integer Lamports for deal calculations to avoid float/currency exchange drift.

---

## 5. 🚀 FastAPI & Async Patterns
- **Async/Await**: Use `async`/`await` for all I/O operations (HTTP requests with `aiohttp`, background jobs).
- **Lean Route Handlers**: Keep route handlers focused and delegate business logic to service/helper modules (`fetcher.py`, `db.py`).
- **Error Handling**: Implement robust error handling around network calls with try/except blocks and graceful fallback to cache or sample data (`data2.json`).

---

## 6. 🎨 Frontend & Templates (Jinja2 + Minimal Modern CSS)
- **Semantic HTML**: Clean, lightweight HTML5 templates extending `base.html`.
- **Modern CSS**: Embedded/inline modern CSS featuring dark theme, flexbox/grid layout, CSS variables, and responsive tables.
- **Vanilla JS**: Use lightweight vanilla JavaScript for interactivity (fetch calls for manual refresh, sortable tables, tooltips for score explainability).

---

## 7. 🧹 Code Cleanliness & Style
- **Type Annotations**: Use Python 3.10+ modern type hints (`int | None`, `list[dict]`, `dict[tuple[str, int], tuple[float, int]]`).
- **Explicit Logging**: Use standard `logging` for tracking background job runs, errors, and fetch cycles.
- **Documentation**: Preserve existing docstrings and comments. Comment non-obvious algorithms (e.g., HBDS scoring logic).
