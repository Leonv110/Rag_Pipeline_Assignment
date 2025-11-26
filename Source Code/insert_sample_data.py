import os
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi


# Load environment variables (reads from the .env file)
load_dotenv()

# --- PostgreSQL Data Insertion (1000+ Records, 2 Tables) ---
def insert_postgres_data():
    conn = None
    try:
        print("Attempting to connect to PostgreSQL (Neon)...")
        # SSL mode is required for secure cloud connections like Neon
        conn = psycopg2.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            sslmode='require' 
        )
        cur = conn.cursor()
        
        # --- 1. USERS TABLE (1000 Records) ---
        cur.execute("DROP TABLE IF EXISTS orders;") # Drop dependent table first
        cur.execute("DROP TABLE IF EXISTS users;")
        cur.execute("""
            CREATE TABLE users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50),
                role VARCHAR(50),
                department VARCHAR(50),
                created_at TIMESTAMP
            );
        """)
        
        print("Inserting 1000 records into 'users'...")
        cur.execute("""
            INSERT INTO users (username, role, department, created_at)
            SELECT
                'user_' || i::text, 
                CASE WHEN i % 10 = 0 THEN 'Manager' ELSE 'Staff' END, 
                CASE (i % 5) 
                    WHEN 0 THEN 'Sales' 
                    WHEN 1 THEN 'IT' 
                    WHEN 2 THEN 'HR' 
                    WHEN 3 THEN 'Finance' 
                    ELSE 'R&D' 
                END,
                NOW() - (random() * INTERVAL '365 days') 
            FROM generate_series(1, 1000) AS s(i);
        """)
        
        # --- 2. ORDERS TABLE (1500 Records) ---
        cur.execute("""
            CREATE TABLE orders (
                order_id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(user_id),
                product_name VARCHAR(100),
                amount DECIMAL(10, 2),
                order_date TIMESTAMP
            );
        """)
        
        print("Inserting 1500 records into 'orders'...")
        cur.execute("""
            INSERT INTO orders (user_id, product_name, amount, order_date)
            SELECT
                (random() * 999 + 1)::INT, 
                'Product_' || (i % 50 + 1)::text,
                (random() * 1000)::numeric(10, 2), 
                NOW() - (random() * INTERVAL '180 days')
            FROM generate_series(1, 1500) AS s(i);
        """)

        conn.commit()
        print("✅ PostgreSQL: 1000+ records inserted into 'users' (2 tables created).")
        
    except Exception as e:
        print(f"❌ PostgreSQL Error (Check .env and Neon firewall rules): {e}")
    finally:
        if conn:
            conn.close()

# --- MongoDB Data Insertion (1000 Documents, 1 Collection) ---
def insert_mongodb_data():
    client = None
    try:
        print("Attempting to connect to MongoDB (Atlas)...")
        # The MongoClient automatically handles the complex connection string
        client = MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
        db = client[os.getenv("MONGO_DB_NAME")]
        collection = db.projects
        
        collection.delete_many({}) 
        
        # Generate 1000 synthetic documents
        documents = []
        for i in range(1, 1001):
            status = ["Active", "Completed", "On Hold"][i % 3]
            priority = ["High", "Medium", "Low"][i % 3]
            
            doc = {
                "project_id": f"PRJ-{i:04d}",
                "name": f"Project Name {i}",
                "status": status,
                "priority": priority,
                "description": f"Detailed description for Project {i}. This project involves complex data migration and ETL pipelines.",
                "tasks_count": i % 50 + 10,
                "team_size": i % 10 + 2,
            }
            documents.append(doc)
        
        print(f"Inserting {len(documents)} documents into 'projects'...")
        collection.insert_many(documents)
        
        print(f"✅ MongoDB: {len(documents)} records inserted into 'projects' collection.")
        
    except Exception as e:
        print(f"❌ MongoDB Error (Check .env and Atlas IP access rules): {e}")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    insert_postgres_data()
    insert_mongodb_data()