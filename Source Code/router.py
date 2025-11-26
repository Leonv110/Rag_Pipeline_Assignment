from typing import List

# Mapping of keywords to the internal source keys used in the pipeline
SOURCE_MAPPING = {
    "PostgreSQL_User": ["user", "profile", "employee", "staff"],
    "PostgreSQL_Order": ["order", "purchase", "amount", "transaction", "product"],
    "MongoDB_Project": ["project", "document", "task", "pipeline", "status"], 
    "REST_API_Country": ["country", "capital", "population", "region", "city"],
    "Redis_Data": ["status", "cache", "critical", "live"]
}

def route_query(query: str) -> List[str]:
    """
    Analyzes the user query to determine the list of relevant data sources 
    using a simple keyword matching strategy.

    Args:
        query: The natural language question asked by the user.

    Returns:
        A list of string keys corresponding to the relevant data retrieval functions.
    """
    query_lower = query.lower()
    
    # --- Priority 1: Multi-Source Query Check (Required Demonstration Case) ---
    if ("project" in query_lower or "pipeline" in query_lower) and \
       any(keyword in query_lower for keyword in ["user", "employee", "staff"]):
        print("[ROUTING] Identified a MULTI-SOURCE query (PG User + Mongo Project).")
        return ["PostgreSQL_User", "MongoDB_Project"]

    # --- Priority 2: Single-Source Keyword Matching ---
    determined_sources: List[str] = []
    
    for source_key, keywords in SOURCE_MAPPING.items():
        if any(keyword in query_lower for keyword in keywords):
            determined_sources.append(source_key)
            
    # --- Priority 3: Fallback ---
    if not determined_sources:
        # Default to a general source if no specific keywords are found
        determined_sources.append("MongoDB_Project")
        
    return list(set(determined_sources))

# Example Verification 
if __name__ == "__main__":
    print("--- Running Query Router Verification ---")
    
    query_1 = "Show me the role of a staff user."
    print(f"\nQuery: '{query_1}'")
    print(f"Sources: {route_query(query_1)}") 
    
    query_2 = "Show me project pipeline details and related user employee data."
    print(f"\nQuery: '{query_2}'")
    print(f"Sources: {route_query(query_2)}")
    
    query_3 = "What is the capital and population of Germany?"
    print(f"\nQuery: '{query_3}'")
    print(f"Sources: {route_query(query_3)}")