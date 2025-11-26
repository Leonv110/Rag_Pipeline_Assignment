import os
import json
import psycopg2
from pymongo import MongoClient
import redis
import requests
from dotenv import load_dotenv
import ssl
from typing import List, Optional

# Load environment variables
load_dotenv()

# --- 1. PostgreSQL Connector (Structured Data) ---

def get_pg_user_data(query_term: str, limit: int = 3) -> str:
    """
    Retrieves user data from PostgreSQL (Neon), returning a structured string.

    Args:
        query_term: The keyword to search across username, role, or department.
        limit: The maximum number of records to retrieve (Result Limiting).

    Returns:
        A string containing formatted user data or an error message.
    """
    conn = None
    data_list: List[str] = []
    try:
        conn = psycopg2.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            sslmode='require'
        )
        cur = conn.cursor()
        
        query = f"""
            SELECT username, role, department 
            FROM users 
            WHERE username ILIKE %s OR role ILIKE %s OR department ILIKE %s 
            LIMIT {limit};
        """
        term_pattern = f"%{query_term}%" 
        cur.execute(query, (term_pattern, term_pattern, term_pattern)) 
        
        results = cur.fetchall()
        
        for row in results:
            data_list.append(f"PG_USER: Username: {row[0]}, Role: {row[1]}, Department: {row[2]}")
            
    except Exception as e:
        return f"PG_ERROR: Could not retrieve user data. Error: {e}"
    finally:
        if conn:
            conn.close()
            
    return "\n".join(data_list) if data_list else "PG_USER: No relevant user data found."


def get_pg_order_data(query_term: str, limit: int = 3) -> str:
    """
    Retrieves order data from PostgreSQL (Neon), based on product name.

    Args:
        query_term: The keyword to search across product names.
        limit: The maximum number of records to retrieve (Result Limiting).

    Returns:
        A string containing formatted order data or an error message.
    """
    conn = None
    data_list: List[str] = []
    try:
        conn = psycopg2.connect(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            sslmode='require' 
        )
        cur = conn.cursor()
        
        query = f"""
            SELECT order_id, product_name, amount, order_date 
            FROM orders 
            WHERE product_name ILIKE %s 
            LIMIT {limit};
        """
        term_pattern = f"%{query_term}%" 
        cur.execute(query, (term_pattern,)) 
        
        for row in cur.fetchall():
            data_list.append(f"PG_ORDER: ID: {row[0]}, Product: {row[1]}, Amount: {row[2]}, Date: {row[3]}")
            
    except Exception as e:
        return f"PG_ERROR: Could not retrieve order data. Error: {e}"
    finally:
        if conn:
            conn.close()
            
    return "\n".join(data_list) if data_list else "PG_ORDER: No relevant order data found."


# --- 2. MongoDB Connector (Document Data) ---

def get_mongo_project_data(query_term: str, limit: int = 3) -> str:
    """
    Retrieves project documents from MongoDB (Atlas), returning a structured JSON string.

    Args:
        query_term: The keyword to search across project name or description.
        limit: The maximum number of documents to retrieve (Result Limiting).

    Returns:
        A string containing formatted JSON project data or an error message.
    """
    client = None
    data_list: List[str] = []
    try:
        # Robust SSL fix for Windows/Atlas connection conflicts
        client = MongoClient(
            os.getenv("MONGO_URI"), 
            tls=True, 
            tlsAllowInvalidCertificates=True 
        )
        db = client[os.getenv("MONGO_DB_NAME")]
        collection = db.projects
        
        # Retrieval with result limiting
        search_query = {
            "$or": [
                {"name": {"$regex": query_term, "$options": "i"}},
                {"description": {"$regex": query_term, "$options": "i"}}
            ]
        }
        
        results = collection.find(search_query).limit(limit)
        
        for doc in results:
            doc.pop('_id', None) 
            data_list.append(f"MONGO_PROJECT: {json.dumps(doc)}")
            
    except Exception as e:
        return f"MONGO_ERROR: Could not retrieve data. Error: {e}"
    finally:
        if client:
            client.close()
            
    return "\n".join(data_list) if data_list else "MONGO_PROJECT: No relevant project data found."

# --- 3. REST API Connector (External Service) ---

def get_api_country_data(country_name: str) -> str:
    """
    Retrieves public country data via a REST API (REST Countries API).

    Args:
        country_name: The specific name of the country to query.

    Returns:
        A string containing formatted JSON country data or an error message.
    """
    BASE_URL = "https://restcountries.com/v3.1/name/"
    try:
        response = requests.get(f"{BASE_URL}{country_name}?fullText=true") 
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            return f"API_COUNTRY: No country data found for '{country_name}'."
            
        country_info = data[0]
        context = {
            "name": country_info.get('name', {}).get('common'),
            "capital": country_info.get('capital', ['N/A'])[0],
            "region": country_info.get('region'),
            "population": country_info.get('population')
        }
        
        return f"API_COUNTRY: {json.dumps(context)}"
        
    except requests.exceptions.RequestException as e:
        return f"API_ERROR: Failed to connect or retrieve data: {e}"
    except Exception as e:
        return f"API_ERROR: General error during API call: {e}"

# --- 4. Redis Connector (Caching/KV Store) ---

def set_redis_cache(key: str, value: str, expiry_seconds: int = 3600) -> bool:
    """
    Stores the final LLM response in Redis for cost optimization.

    Args:
        key: The hash of the query string.
        value: The LLM's generated response.
        expiry_seconds: Time to live (TTL) for the cache entry.

    Returns:
        True if set successful, False otherwise.
    """
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST"), 
            port=int(os.getenv("REDIS_PORT")), 
            password=os.getenv("REDIS_PASSWORD")
        )
        r.ping() 
        r.set(key, value, ex=expiry_seconds)
        return True
    except Exception as e:
        print(f"[CACHE_ERROR] Failed to set cache: {e}")
        return False

def get_redis_cache(key: str) -> Optional[str]:
    """
    Retrieves cached LLM response from Redis.

    Args:
        key: The hash of the query string.

    Returns:
        The cached string response if found, otherwise None.
    """
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST"), 
            port=int(os.getenv("REDIS_PORT")), 
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True 
        )
        r.ping() 
        return r.get(key)
    except Exception as e:
        print(f"[CACHE_ERROR] Failed to get cache: {e}")
        return None

# --- Verification Block ---
if __name__ == "__main__":
    print("--- Running Data Connector Verification ---")
    
    print("\n[TEST] PG User (Searching for 'Manager' role):")
    print(get_pg_user_data("Manager"))
    
    print("\n[TEST] MONGO Project (Searching for 'pipeline' project):")
    print(get_mongo_project_data("pipeline"))
    
    print("\n[TEST] API Country (Searching for 'Germany'):")
    print(get_api_country_data("Germany"))
    
    test_key = "test_status"
    set_redis_cache(test_key, "System Operational")
    print("\n[TEST] REDIS Key set.")
    print(f"[RESULT] REDIS Key retrieval: {get_redis_cache(test_key)}")