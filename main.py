import os
from pathlib import Path

# Load environment variables from .env file for local development
def load_environment():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# Load environment before importing app
load_environment()

from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
