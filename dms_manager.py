import sqlite3
import os

# simple Document Management System for government records, focusing on indexing and tracking document lifecycle.

def initialize_database():
    conn = sqlite3.connect('gov_records.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_records (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_type TEXT NOT NULL,
            reference_number TEXT UNIQUE NOT NULL,
            date_filed DATE DEFAULT CURRENT_DATE,
            storage_location TEXT,
            status TEXT DEFAULT 'Archived'
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_type ON document_records(doc_type);")
    
    conn.commit()
    conn.close()
    print("Database schema initialized successfully.")

def index_documents_to_db(directory_path):
    conn = sqlite3.connect('gov_records.db')
    cursor = conn.cursor()
    
    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            try:
                parts = filename.replace('.pdf', '').split('_')
                doc_type, ref_num = parts[0], parts[1]
                
                cursor.execute("""
                    INSERT INTO document_records (doc_type, reference_number, storage_location)
                    VALUES (?, ?, ?)
                """, (doc_type, ref_num, "Cabinet_A_Shelf_1"))
            except Exception as e:
                print(f"Skipping file {filename}: {e}")
                
    conn.commit()
    conn.close()
    print("Document indexing complete.")

if __name__ == "__main__":
    initialize_database()