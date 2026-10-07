"""Keep MetaGPT's runtime config, logs and generated metadata inside the run folder."""
import os
from pathlib import Path


def prepare_runtime(root):
    runtime = Path(root).resolve() / 'metagpt-runtime'
    config = runtime / 'config'
    config.mkdir(parents=True, exist_ok=True)
    # Custom Actions use the existing model gateway. This config only satisfies
    # MetaGPT's import-time client configuration; it contains no real credential.
    (config / 'config2.yaml').write_text(
        'llm:\n  api_type: openai\n  model: action-gateway\n'
        '  api_key: unused-by-custom-actions\n  base_url: http://127.0.0.1:1/v1\n', encoding='utf-8')
    os.environ['METAGPT_PROJECT_ROOT'] = str(runtime)
