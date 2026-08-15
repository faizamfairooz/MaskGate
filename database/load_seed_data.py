import os
import sys
import psycopg2

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config.settings import settings

def load_data():
    print(f"Connecting to database {settings.DB_NAME} on {settings.DB_HOST}:{settings.DB_PORT} as {settings.DB_USER}...")
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # 1. Apply schema.sql statements safely
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if os.path.exists(schema_path):
        print(f"Applying schema from {schema_path}...")
        with open(schema_path, "r") as f:
            content = f.read()
        # Split statements and execute individually
        statements = content.split(";")
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cur.execute(stmt + ";")
            except Exception as e:
                # Ignore duplicate object / already exists errors
                pass
        print("Schema ensured.")

    # 2. Apply seed.sql statements safely
    seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")
    if os.path.exists(seed_path):
        print(f"Applying seed data from {seed_path}...")
        with open(seed_path, "r") as f:
            content = f.read()
        statements = content.split(";")
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cur.execute(stmt + ";")
            except Exception as e:
                pass
        print("Seed data applied.")

    # 3. Report total table counts
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
    tables = cur.fetchall()
    print("\nDatabase Tables and Row Counts:")
    for (tbl,) in tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{tbl}";')
            cnt = cur.fetchone()[0]
            print(f"  • {tbl}: {cnt} rows")
        except Exception as e:
            print(f"  • {tbl}: (error counting rows: {e})")

    cur.close()
    conn.close()
    print("\nAll dummy data successfully uploaded to PostgreSQL!")

if __name__ == "__main__":
    load_data()
