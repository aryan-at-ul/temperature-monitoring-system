import psycopg2
from psycopg2 import sql
from tabulate import tabulate
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "dbname": "temperature_db",
    "user": "tm_user",
    "password": "tm_pass",
    "host": "localhost",
    "port": 5432,
}
REPORT_PATH      = Path("temperature_db_report.txt")
SAMPLE_ROWS      = 5            # number of rows to preview from each table
INCLUDE_SCHEMAS  = ["public"]   # schemas whose tables you want to preview

# ──────────────────────────────────────────────────────────────────────────────
# Section queries
# ──────────────────────────────────────────────────────────────────────────────
QUERIES = {
    "Databases": "SELECT datname FROM pg_database WHERE datistemplate = false;",
    "Tables in public schema": """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type='BASE TABLE';
    """,
    "Views in public schema": """
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public';
    """,
    "Roles/Users": """
        SELECT rolname, rolsuper, rolcreaterole, rolcreatedb, rolcanlogin
        FROM pg_roles;
    """,
    "Privileges": """
        SELECT grantee, table_name, privilege_type
        FROM information_schema.role_table_grants
        WHERE table_schema = 'public'
        ORDER BY table_name, grantee;
    """,
    "Partitions (if any)": """
        SELECT inhrelid::regclass AS partition_name
        FROM pg_inherits
        WHERE inhparent = 'temperature_readings_history'::regclass;
    """,
}

# ──────────────────────────────────────────────────────────────────────────────
# Helper: fetch sample rows from a table
# ──────────────────────────────────────────────────────────────────────────────
def fetch_sample_rows(cursor, schema: str, table: str, limit: int = SAMPLE_ROWS):
    query = sql.SQL("SELECT * FROM {}.{} LIMIT {}").format(
        sql.Identifier(schema),
        sql.Identifier(table),
        sql.Literal(limit),
    )
    cursor.execute(query)
    rows = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]
    return headers, rows

# ──────────────────────────────────────────────────────────────────────────────
# Main report generator
# ──────────────────────────────────────────────────────────────────────────────
def generate_report():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn, open(REPORT_PATH, "w") as f:
            cur = conn.cursor()

            f.write("📊 Temperature Monitoring Database Report\n")
            f.write("=" * 60 + "\n\n")

            # 1️⃣  High-level sections (existing summary)
            for section, query in QUERIES.items():
                f.write(f"## {section}\n\n")
                try:
                    cur.execute(query)
                    rows = cur.fetchall()
                    if rows:
                        headers = [desc[0] for desc in cur.description]
                        f.write(tabulate(rows, headers=headers, tablefmt="grid"))
                    else:
                        f.write("No data found.")
                except Exception as e:
                    f.write(f"⚠️  Error in section '{section}': {e}")
                f.write("\n\n")

            # 2️⃣  Sample rows for every table
            f.write("## Sample Rows Per Table\n\n")
            # fetch tables once
            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema = ANY(%s) AND table_type='BASE TABLE'
                ORDER BY table_schema, table_name;
                """,
                (INCLUDE_SCHEMAS,),
            )
            tables = cur.fetchall()

            if not tables:
                f.write("No base tables found.\n")
            else:
                for schema, table in tables:
                    f.write(f"### {schema}.{table}\n\n")
                    try:
                        headers, rows = fetch_sample_rows(cur, schema, table)
                        if rows:
                            f.write(tabulate(rows, headers=headers, tablefmt="grid"))
                        else:
                            f.write("(table is empty)")
                    except Exception as e:
                        f.write(f"⚠️  Error reading {schema}.{table}: {e}")
                    f.write("\n\n")

        print(f"✅ Report generated: {REPORT_PATH.resolve()}")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    generate_report()

