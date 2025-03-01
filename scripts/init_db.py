from common.database.connection import init_db
import os
import sys

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("Initializing database...")
    engine, _ = init_db()
    print(f"Database created at {engine.url}")
    print("Done! Database initialized.")

if __name__ == "__main__":
    main() 