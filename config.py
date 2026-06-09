"""Create tables, seed the activity catalog, and generate a demo study with
synthetic data (including a cyclical accounting month-end peak).

Run from the project root:   python -m scripts.init_db
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import create_all, SessionLocal
from seed.synthetic import generate_demo


def main():
    create_all()
    s = SessionLocal()
    try:
        study_id = generate_demo(s)
        print(f"Demo study created: {study_id}")
    finally:
        s.close()


if __name__ == "__main__":
    main()
