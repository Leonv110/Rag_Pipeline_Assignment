### RAG Pipeline Design Document: Multi-Source Data Integration POC
---
## **1. Architecture Overview**

The system operates in a sequential, modular pipeline, where the user query is progressively enriched and answered by discrete components.

1.1 **Component Breakdown and Responsibilities**

| Component                       | Responsibility                                                                      | Status in POC                           |
|---------------------------------|--------------------------------------------------------------------------------------|-------------------------------------------|
| **Query Router (router.py)**    | Analyzes query intent to determine which external data source(s) are relevant.       | Implemented (Keyword Matching)            |
| **Retrieval Layer (data_connectors.py)** | Manages connectivity and executes native queries (SQL, Mongo, HTTP GET).   | Implemented (4 Sources: PG, Mongo, API, Redis) |
| **Caching Layer (Redis Cloud)** | Stores the final LLM response against the query hash for instant retrieval and cost savings. | Implemented (Cache Check & Store) |
| **Context Manager (pipeline.py)** | Combines retrieved data into a single context prompt and enforces content limits. | Implemented (Combination & Truncation) |
| **Generation Layer (Ollama/Llama3)** | Synthesizes the final natural language answer based only on the provided context. | Implemented (Local LLM Execution) |


1.2 **Basic Data Flow**

1. Input: User query enters pipeline.py.

2. Cache Check: Query is hashed; Redis is checked for an existing answer (CACHE HIT or MISS).

3. Routing (MISS): router.py receives the query and selects relevant data sources (e.g., PostgreSQL_User, MongoDB_Project).

4. Retrieval: data_connectors.py calls the appropriate cloud services.

5. Context Creation: Retrieved data snippets (e.g., SQL rows, JSON objects, API results) are combined into a final context string.

6. Generation: The context and query are sent to the Ollama Llama3 model.

7. Output: The LLM's response is returned to the user and saved in Redis for future requests.

---

## **2. Data Integration Strategy**

All data sources are hosted on free cloud tiers to avoid local setup issues, connected via dedicated Python drivers.

| Source              | Connection Method                                                                                     | Query Strategy                                                                                                 | Simple Error Handling                                                                                         |
|---------------------|--------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| **PostgreSQL (Neon)** | psycopg2 driver using secure `sslmode='require'` with individual credentials.                           | SQL Query: Used standard `SELECT` statements with `ILIKE` for case-insensitive search across key fields.        | `try/finally` block ensures the database connection is always closed.                                         |
| **MongoDB (Atlas)** | pymongo driver using the Atlas connection string.                                                      | Document Query: Used `$regex` inside an `$or` query for fuzzy search on name and description fields.            | Explicit `tls=True` and `tlsAllowInvalidCertificates=True` to bypass Windows/Atlas SSL handshake issues.      |
| **REST API (Countries)** | Python `requests` library.                                                                             | HTTP GET: Simple `/name/{query_param}` search.                                                                  | `response.raise_for_status()` catches HTTP 4xx/5xx (e.g., 404).                                               |
| **Redis (Redis Cloud)** | redis-py client.                                                                                     | Key-Value lookups using query hash as key (`GET`/`SET`).                                                        | `r.ping()` on connect + graceful exception handling so cache failures don’t stop pipeline execution.          |
| **Kafka (Omitted)** | N/A                                                                                                    | Omitted due to scope and time prioritization.                                                                   | N/A                                                                                                            |


---

## **3. Retrieval Strategy**

**3.1 Which Sources to Query (Intelligent Querying)**

**Solution: Simple Keyword Matching (`router.py`)**
The router converts the query to lowercase and matches it against a predefined dictionary of keywords
(e.g., `"project"`, `"user"`, `"capital"`).
This determines which external data sources (PostgreSQL, MongoDB, API, Redis) should be queried.


 **3.2 Alternative Approaches (Not Used in the POC)**

**🔹 Vector Search & Semantic Routing**

* Embed user queries using models such as **BGE** or **E5**
* Perform semantic search using vector stores like **ChromaDB** or **Qdrant**
* Improves understanding beyond keyword matching

 **🔹 LLM Agent / Tool Calling**

* Use a smaller LLM to generate **SQL**, **MongoDB queries**, or API calls dynamically
* Removes reliance on static routing
* Produces more accurate retrieval for complex queries


**3.3 Relevance and Ranking**

**Solution: Explicit Targeting + Top-N Selection**

* Each database retrieves only the most relevant fields
  (e.g., `username ILIKE '%user_10%'`)
* Ensures retrieved data is relevant and focused

**Ranking Behavior:**

* Native database ordering is used
* Results are explicitly limited using `LIMIT 3`
* Guarantees only the **top 3 most relevant entries** per source are added to the context window
* Helps keep prompt size manageable before sending to the LLM



---

## **4. Context Management**

**Context Window Limits**

* **Solution 1 (Preventative): Result Limiting — `LIMIT 3`**
  PostgreSQL and MongoDB retrieval functions always use `LIMIT 3` to pull only the highest-ranking, most essential results.
  This keeps the context small before combining data from multiple sources.

* **Solution 2 (Reactive): Context Truncation (`pipeline.py`)**
  After all data is combined, if the context string exceeds **10,000 characters** (`MAX_CONTEXT_CHARS`), the system truncates it.
  This ensures the prompt always fits within the Llama3 model’s context window.



**Document Selection**

* Uses an **Aggregation by Source** strategy.
* Retrieved snippets from each source are **not cross-ranked**; instead, they are appended in clearly labeled blocks
  (e.g., `<PG_USER> ... </PG_USER>`, `<MONGO_PROJECT> ... </MONGO_PROJECT>`).
* The LLM is responsible for identifying relevant information within this structured, multi-source context.

---


## **5. Cost Optimization**

**Basic Caching Strategy**

* **Solution: Query Hashing + Redis Caching**
  The raw user query is hashed using **SHA256** to generate a unique, deterministic key.

* **Cache Check**
  Redis is queried using this hash key.
  If a matching entry exists (**CACHE HIT**), the stored response is returned immediately—
  **skipping database access + LLM generation costs**.

* **Cache Store**
  After generating a response via the LLM, the output is cached in Redis with a
  **1-hour TTL**, ensuring fast repeat queries while avoiding stale results.


**Token Tracking Approach**

* **Solution: Preventative Token Optimization**
  Full token tracking was postponed as non-essential for the POC.
  Instead, token usage is reduced *before* the LLM call by:

  * Using **LIMIT 3** on all SQL/Mongo queries
  * Applying **context truncation** at **10,000 characters**

This minimizes unnecessary prompt size and reduces computational cost.


**Model Selection Rationale**

* **Solution: Use Ollama + Llama3 (Local Model)**
  Running the LLM locally completely eliminates:

  * Paid API usage
  * Token-based billing
  * Network latency

This makes it the most cost-effective choice for development and internal testing environments.

