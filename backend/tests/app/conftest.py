import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def load_settings(tmp_path):
    """Import settings in a fresh process with an isolated .env and working dir."""
    backend = tmp_path / "backend"
    app = backend / "app"
    app.mkdir(parents=True)
    source = Path(__file__).resolve().parents[2] / "app" / "settings.py"
    target = app / "settings.py"
    target.write_text(source.read_text())
    working_dir = tmp_path / "another-directory"
    working_dir.mkdir()
    script = """
import json
import runpy
import sys

settings = runpy.run_path(sys.argv[1])
print(json.dumps({
    'debug': settings['DEBUG'],
    'hosts': settings['ALLOWED_HOSTS'],
    'database': settings['DATABASES']['default'],
    'secret': settings['SECRET_KEY'],
}))
"""

    def load(file_values=None, environment=None, *, check=True):
        values = {"DJANGO_SECRET": "test-settings-secret"}
        if file_values is not None:
            values = file_values
        (backend / ".env").write_text(
            "\n".join(f"{key}={value}" for key, value in values.items())
        )
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("DB_")
            and key not in {"DEBUG", "ALLOWED_HOSTS", "DJANGO_SECRET"}
        }
        env.update(environment or {})
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", script, str(target)],
            cwd=working_dir,
            env=env,
            capture_output=True,
            text=True,
            check=check,
        )
        return json.loads(result.stdout) if check else result

    return load
