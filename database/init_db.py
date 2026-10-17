import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db import init_db
from config import Config


def main():
    print("[*] Initializing LibraFlow database tables...")
    db_path = Config.DATABASE_PATH
    print(f"[*] Target database: {db_path}")
    init_db(db_path)
    print("[+] Database tables created successfully with foreign keys enabled.")


if __name__ == "__main__":
    main()
