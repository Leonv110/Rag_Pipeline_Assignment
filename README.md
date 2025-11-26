
---

# **Multi-Source RAG Pipeline POC**

This project implements a **Retrieval-Augmented Generation (RAG)** pipeline designed to aggregate information from **four heterogeneous data sources**:

* PostgreSQL
* MongoDB
* REST API
* Redis

It demonstrates **intelligent query routing**, **context construction**, and **caching for cost optimization**, powered by a **local LLM (Ollama + Llama3)**.

---

## 🚀 **Deliverables**

This repository contains:

* `pipeline.py` – Main orchestration pipeline
* `router.py` – Query routing logic
* `data_connectors.py` – Connectivity + data retrieval
* Documentation files (architecture, strategy breakdown, demo logs)

---

## 🛠️ **Setup Instructions**

### **1. Prerequisites (External Services)**

To run this POC, the following services must be accessible (free cloud tiers recommended):

| Service         | Requirement                          |
| --------------- | ------------------------------------ |
| **LLM Service** | Ollama installed and running locally |
| **PostgreSQL**  | Neon instance                        |
| **MongoDB**     | Atlas Cluster                        |
| **Redis**       | Redis Cloud instance                 |
| **REST API**    | REST Countries API (public)          |

---

### **2. Dependencies and Installation**

**Step 1 — Clone the repository or unzip the project folder.**

**Step 2 — Create `requirements.txt` in the project root:**

```
psycopg2-binary
pymongo
redis
requests
python-dotenv
ollama
```

**Step 3 — Install dependencies:**

```
pip install -r requirements.txt
```

---

## **3. Environment Variables (`.env`)**

Create a file called `.env` in the root directory:

| Variable                                                    | Purpose                | Notes                            |
| ----------------------------------------------------------- | ---------------------- | -------------------------------- |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, etc. | PostgreSQL credentials | Points to your Neon instance     |
| `MONGO_URI`, `MONGO_DB_NAME`                                | MongoDB connection     | Ensure your IP is whitelisted    |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`                | Redis Cloud access     | Used for caching                 |
| `OLLAMA_API_URL`                                            | Ollama endpoint        | Usually `http://localhost:11434` |
| `OLLAMA_MODEL_NAME`                                         | LLM model              | Default: `llama3`                |

---

## 🏃 **How to Run the POC**

The demo is executed by running `pipeline.py`, which triggers:

* Query routing
* Database/API retrieval
* Context building
* LLM generation
* Caching (Redis)

---

### **Step 1: Initialize the Data (Run Once)**

This script populates:

* PostgreSQL → two tables (1000+ rows)
* MongoDB → one collection (1000 documents)

```
python insert_sample_data.py
```

---

### **Step 2: Start the LLM Server (Separate Window)**

Open a new terminal:

```
ollama serve
```

---

### **Step 3: Run the Pipeline and Capture Output**

Recommended: Save output to a file for submission.

```
python pipeline.py > Output.txt
```

This will run **four core test cases**:

1. **Single Source Query**
   Retrieves data from PostgreSQL only.

2. **Multi-Source Query**
   Routes to **PostgreSQL + MongoDB**.

3. **API Integration**
   Fetches data from the REST Countries API.

4. **Caching Test**
   Re-runs API query → expected **CACHE HIT**, proving cost optimization.

The contents of **Output.txt** serve as the required *Sample Output* for your assignment.

---

