import os
from dotenv import load_dotenv
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
env_path = base_dir / ".env"

print(f"Cargando .env desde: {env_path}")

load_dotenv(env_path)
