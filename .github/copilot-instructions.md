## Quick orientation for AI coding agents

This repo is a small Flask web app (single-module entry) with most business logic in `services/`.

Overview
- Entry point: `main.py` — Flask app. When run directly it calls `app.run('localhost', 4449)`.
- Services: `services/__init__.py` exports `Wikipedia_reader`, `Youtube_reader`, `My_DV`, `Portfolio_Base`, and `Pusher_handler`.
- Config: `cfg/.config` (JSON) contains DB creation SQL and PUSHER credentials.
- Secrets: Flask secret is read from `./.flask_key.txt` at startup.

How to run (developer flow)
- Install deps: `pip install -r requirements.txt`.
- Start locally: `python3 main.py` (app listens on `localhost:4449`).

Key code patterns and conventions (project-specific)
- Database creation & schema: `Portfolio_Base.__init__` reads `cfg/.config['DB_CREATION']` and runs SQL to create schema when DB file is missing or empty. Edit DB schema by updating `cfg/.config` rather than sprinkling SQL in code.
- DB access: use `Portfolio_Base.exec_statement(stmt, wiki_id=None)` and `Portfolio_Base.db_insert(...)` for all DB interactions — these centralize error logging into the `errors` table.
- Logging: `Portfolio_Base.set_up_logging()` configures per-class loggers. Avoid adding ad-hoc print statements unless debugging; prefer `self.logger.debug/info/error`.
- Templates: views call `render_template(..., content=...)` and expect `content` to hold dicts shaped in `main.py` (see `get_db`, `get_keys`, `view_topic`).

Integration & external systems
- Pusher: `PUSHER` credentials live in `cfg/.config`. `main.py` calls `Pusher_handler` in `after_request` and `site_traffic` for realtime events.
- YouTube / Wikipedia: `services/wiki_youtube_reader.py` contains the scraping/API logic. These classes write into the site DB using `db_insert`.
- Data analysis: `services/data_analysis.py` (`My_DV`) generates matplotlib graphs in-memory (backend `agg`) and returns base64 PNGs used by templates.

Files to inspect first when changing behavior
- `main.py` — routing, session setup, and top-level flows.
- `services/portfolio_base.py` — DB handling, logging, config loading.
- `cfg/.config` — configuration keys: `DB_CREATION`, `PUSHER`, `graph_cfg` etc.
- `DB/` — runtime sqlite DBs (do not edit these unless intentional).

Concrete examples
- Read config in a service: `with open(cfg, 'r') as cf: self.config = json.loads(cf.read())` (see `Portfolio_Base.__init__`).
- Insert wikipedia row: `self.db_insert(table_name='Wikipedia', my_id=..., search_text=..., title=..., url=..., description=..., thumbnail=...)`.

Quick gotchas
- The app expects `./.flask_key.txt` to exist with a secret; local runs will fail without it.
- `get_base_uri()` chooses a `base_uri` that affects how DB paths are constructed (local vs PythonAnywhere). Check how `session['base_uri']` is built in `main.py`'s context processor.
- Pusher calls are in `after_request` — modifying or removing them will change site traffic telemetry.

If you want more detail, tell me which area to expand (DB schema, config keys, wiki/youtube reader behavior, or the Pusher/traffic flow) and I will update this file.

—end—## Quick orientation for AI coding agents

This repo is a small Flask web app (single-module entry) with a `services/` package housing most business logic. Use these concrete notes to make safe, effective edits.

- Entry point: `main.py` — a Flask app that runs on `localhost:4449` when started with `python3 main.py`.
- Services: `services/__init__.py` exposes key classes: `Wikipedia_reader`, `Youtube_reader`, `My_DV`, `Portfolio_Base`, `Pusher_handler`.
- DB and config: persistent data lives under `DB/` (e.g. `DB/portfolio.db`, `DB/site.db`). App configuration is in `cfg/.config` (JSON). Secret key is read from `./.flask_key.txt`.

Key patterns and