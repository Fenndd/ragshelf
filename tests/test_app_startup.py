"""Check the real application import path in a clean, offline process."""

import os
import subprocess
import sys
from textwrap import dedent

from ragshelf.config import REPO_ROOT


def test_app_initializes_model_environment_before_library_imports():
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("HF_", "HUGGINGFACE_", "TRANSFORMERS_", "MINERU_", "RAGSHELF_"))
        and name not in {"DEEPSEEK_API_KEY", "OPENROUTER_API_KEY"}
    }
    env.update(
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        PYTHONDONTWRITEBYTECODE="1",
    )
    code = dedent("""\
        import os
        import sys
        from pathlib import Path

        network_attempts = []

        def forbid_network(event, args):
            if event in {"socket.connect", "socket.getaddrinfo", "socket.gethostbyname"}:
                network_attempts.append(event)
                raise AssertionError("Application import attempted network access")

        def forbid_model_loading(frame, event, arg):
            if event == "call" and frame.f_code.co_name == "from_pretrained":
                raise AssertionError("Application import attempted to load a model")

        def forbid_credentials(*args, **kwargs):
            raise AssertionError("Application import attempted to load credentials")

        sys.addaudithook(forbid_network)
        sys.setprofile(forbid_model_loading)
        import ragshelf.config as config
        config.load_secrets = forbid_credentials

        # Import the actual entry point, including its real transitive imports.
        # No upload or button event is supplied, so no model should be loaded.
        import ragshelf.app.streamlit_app
        sys.setprofile(None)
        from huggingface_hub import constants

        expected_hf_home = config.REPO_ROOT / "models" / "hf"
        assert Path(constants.HF_HOME) == expected_hf_home, "HF cache is outside the project"
        assert Path(constants.HF_HUB_CACHE) == expected_hf_home / "hub"
        assert constants.HF_HUB_DISABLE_TELEMETRY is True
        assert Path(os.environ["MINERU_HOME"]) == config.REPO_ROOT / "models" / "mineru"
        assert os.environ["MINERU_TELEMETRY_DISABLED"] == "1"
        assert not network_attempts, network_attempts
        print("Application cache and telemetry initialization verified offline")
        """)

    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Application cache and telemetry initialization verified offline" in result.stdout
