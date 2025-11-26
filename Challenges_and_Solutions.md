

#  Challenges & Solutions**

This document outlines both the **technical challenges encountered** during the development of the Multi-Source RAG Pipeline POC and the **practical solutions** applied to resolve them. These notes also serve as guidance for future iterations of the system.

---

## **1. Docker Internal Server Error (500)**

**Challenge:**
Attempted to containerize the entire system early in the project.
Docker consistently threw an **Internal Server Error (500)** during service startup.

**Reason:**
Misconfigurations in networking and image setup caused unreliable containers, delaying progress.

**Solution:**
Stopped using Docker entirely for the POC and switched to **fully cloud-hosted free-tier services**:

* PostgreSQL → Neon
* MongoDB → Atlas
* Redis → Redis Cloud

This eliminated environment inconsistencies and allowed focusing on the RAG logic rather than container debugging.

---

## **2. MongoDB Atlas DNS Timeout Error**

**Challenge:**
While running the pipeline, MongoDB raised the error:

> ❌ *"The DNS operation timed out after 20 seconds"*

**Cause:**
Local environment caching issues and temporary Atlas DNS resolution delays.

**Solution:**
Restarted:

* the terminal
* Python process
* MongoDB cluster
* system environment

After reset, the DNS resolution worked and MongoDB queries executed normally.

---

## **3. MongoDB SSL Handshake Failure**

**Challenge:**
Encountered:

> **MONGO_ERROR:** *SSL handshake failed: `<cluster>.mongodb.net:27017`*

**Cause:**
Atlas requires network whitelisting.
Windows machines sometimes have SSL certificate mismatches during TLS negotiations.

**Solution:**

* Enabled **IP Access → "Allow Access From Anywhere" (0.0.0.0/0)** in MongoDB Atlas
* Added TLS overrides in the connection config (for development only):

  ```
  tls=True
  tlsAllowInvalidCertificates=True
  ```

After these changes, MongoDB connectivity stabilized.

---

## **4. Ollama Port Binding Error (Port 11434 Already in Use)**

**Challenge:**
Attempting to start the local LLM server generated the error:

> **Error: listen tcp 127.0.0.1:11434: bind: Only one usage of each socket address is normally permitted**

**Cause:**
Ollama was **already running in the background**, occupying port 11434.

**Solution:**

* Quit Ollama from the taskbar
* End all `ollama.exe` tasks from Task Manager
* Restart Ollama using:

  ```
  ollama serve
  ```

After freeing the port, the local LLM server started normally.

---

