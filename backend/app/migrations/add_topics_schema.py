import sqlite3
import os

DB_PATH = "backend/edumind.db"

def migrate_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("Checking 'learning_materials' table...")
    columns = [col[1] for col in cur.execute("PRAGMA table_info(learning_materials)").fetchall()]
    if "syllabus_json" not in columns:
        print("Adding 'syllabus_json' column to 'learning_materials'...")
        cur.execute("ALTER TABLE learning_materials ADD COLUMN syllabus_json TEXT")
        print("Column 'syllabus_json' added successfully.")
    else:
        print("Column 'syllabus_json' already exists in 'learning_materials'.")

    print("\nChecking 'material_topics' table...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS material_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER NOT NULL,
        user_id VARCHAR(100) NOT NULL,
        subject_code VARCHAR(100) NOT NULL,
        chapter_title VARCHAR(255) NOT NULL,
        chapter_order INTEGER NOT NULL DEFAULT 1,
        topic_title VARCHAR(255) NOT NULL,
        topic_summary TEXT,
        estimated_minutes INTEGER NOT NULL DEFAULT 15,
        order_num INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (material_id) REFERENCES learning_materials(id) ON DELETE CASCADE
    )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS ix_material_topics_material_id ON material_topics(material_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_material_topics_user_id ON material_topics(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_material_topics_subject_code ON material_topics(subject_code)")

    conn.commit()
    conn.close()
    print("Schema migration completed successfully!")

if __name__ == "__main__":
    migrate_schema()

