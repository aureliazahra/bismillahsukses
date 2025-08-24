# backend/migrations/fix_missing_persons_timestamps.py
# Tambah kolom created_at & updated_at jika belum ada (MySQL).
# Jalankan:  python -m backend.migrations.fix_missing_persons_timestamps

from sqlalchemy import text
from backend.config.database import engine

def _column_exists(conn, dbname: str, table: str, column: str) -> bool:
    sql = text("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME   = :tbl
          AND COLUMN_NAME  = :col
    """)
    cnt = conn.execute(sql, {"db": dbname, "tbl": table, "col": column}).scalar()
    return (cnt or 0) > 0

def run():
    table = "missing_persons"
    with engine.begin() as conn:
        dbname = conn.execute(text("SELECT DATABASE()")).scalar()
        if not dbname:
            raise RuntimeError("Tidak bisa membaca nama database aktif (SELECT DATABASE()).")

        need_created = not _column_exists(conn, dbname, table, "created_at")
        need_updated = not _column_exists(conn, dbname, table, "updated_at")

        if not (need_created or need_updated):
            print(f"OK: {table}.created_at & {table}.updated_at sudah ada.")
            return

        clauses = []
        if need_created:
            clauses.append("ADD COLUMN `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP")
        if need_updated:
            clauses.append("ADD COLUMN `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")

        alter_sql = f"ALTER TABLE `{table}`\n  " + ",\n  ".join(clauses) + ";"
        print("Applying migration:\n", alter_sql)
        conn.exec_driver_sql(alter_sql)
        print("Done: kolom timestamp ditambahkan.")

if __name__ == "__main__":
    run()
