import psycopg2
from tabulate import tabulate
from pathlib import Path

# Database connection config
DB_CONFIG = {
    "dbname": "temperature_db",
    "user": "tm_user",
    "password": "tm_pass",
    "host": "localhost",
    "port": 5432
}

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
    """
}

def generate_report():
    report_path = Path("temperature_db_report.txt")

    try:
        with psycopg2.connect(**DB_CONFIG) as conn, open(report_path, "w") as f:
            cursor = conn.cursor()
            f.write("📊 Temperature Monitoring Database Report\n")
            f.write("=" * 60 + "\n\n")

            for section, query in QUERIES.items():
                f.write(f"## {section}\n\n")
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    if rows:
                        headers = [desc[0] for desc in cursor.description]
                        f.write(tabulate(rows, headers=headers, tablefmt="grid") + "\n\n")
                    else:
                        f.write("No data found.\n\n")
                except Exception as e:
                    f.write(f"⚠️ Error in section '{section}': {e}\n\n")

        print(f"✅ Report generated: {report_path.resolve()}")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    generate_report()

