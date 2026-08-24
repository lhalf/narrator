# install dependencies into .venv
sync:
    uv sync

# run the bot (must run from the repo root)
run:
    uv run python src/main.py

test:
    uv run python -m pytest src/command_handler.py

# check every module still imports
check:
    uv run python -m compileall -q src

# re-resolve the lockfile, allowing newer versions
upgrade:
    uv lock --upgrade
