import mysql.connector as mc

CONFIG = {
    "host": "sql12.freesqldatabase.com",
    "port": 3306,
    "user": "sql12795688",
    "password": "VATyekp2U8",
    "database": "sql12795688",
}

def q_all(cnx, sql, params=None):
    cur = cnx.cursor()
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    return rows

def exec1(cnx, sql, params=None):
    cur = cnx.cursor()
    cur.execute(sql, params or ())
    cnx.commit()
    cur.close()

def col_exists(cnx, table, col):
    cur = cnx.cursor()
    cur.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (col,))
    ok = cur.fetchone() is not None
    cur.close()
    return ok

def main():
    cnx = mc.connect(**CONFIG)
    print("✅ Connected. Server version:", q_all(cnx, "SELECT VERSION()")[0][0])

    print("\n-- BEFORE: SHOW COLUMNS --")
    for row in q_all(cnx, "SHOW COLUMNS FROM missing_persons"):
        print(row)

    need_created = not col_exists(cnx, "missing_persons", "created_at")
    need_updated = not col_exists(cnx, "missing_persons", "updated_at")

    if not (need_created or need_updated):
        print("\nℹ️  Columns already exist. Nothing to do.")
    else:
        # 1) Tambah kolom sebagai NULL dulu (aman di semua versi)
        for col in [("created_at", need_created), ("updated_at", need_updated)]:
            name, needed = col
            if not needed: 
                continue
            try:
                exec1(cnx, f"ALTER TABLE missing_persons ADD COLUMN {name} DATETIME NULL")
                print(f"➕ Added column {name} (DATETIME NULL)")
            except mc.Error as e:
                print(f"⚠️  Add {name} DATETIME failed: {e}; trying TIMESTAMP NULL...")
                try:
                    exec1(cnx, f"ALTER TABLE missing_persons ADD COLUMN {name} TIMESTAMP NULL")
                    print(f"➕ Added column {name} (TIMESTAMP NULL)")
                except mc.Error as e2:
                    print(f"💥 Failed to add column {name}: {e2}")

        # 2) Inisialisasi nilai agar tidak ada NULL
        try:
            exec1(cnx, "UPDATE missing_persons "
                       "SET created_at = COALESCE(created_at, NOW()), "
                       "    updated_at = COALESCE(updated_at, NOW())")
            print("✅ Initialized created_at/updated_at with NOW() where NULL")
        except mc.Error as e:
            print(f"⚠️  Cannot initialize values: {e}")

        # 3) Jadikan NOT NULL (selaras dengan model)
        for name in ("created_at", "updated_at"):
            try:
                # Cari tipe yang kepasang (DATETIME atau TIMESTAMP)
                col = q_all(cnx, "SHOW COLUMNS FROM missing_persons LIKE %s", (name,))
                if col:
                    col_type = col[0][1].split('(')[0].upper()  # e.g., 'datetime' -> 'DATETIME'
                    exec1(cnx, f"ALTER TABLE missing_persons MODIFY {name} {col_type} NOT NULL")
                    print(f"🔒 Set {name} NOT NULL ({col_type})")
            except mc.Error as e:
                print(f"⚠️  Could not set {name} NOT NULL: {e}")

    print("\n-- AFTER: SHOW COLUMNS --")
    for row in q_all(cnx, "SHOW COLUMNS FROM missing_persons"):
        print(row)

    cnx.close()
    print("\n🎉 Done.")

if __name__ == "__main__":
    main()
