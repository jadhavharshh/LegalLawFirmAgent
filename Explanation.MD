# Legal Law Firm Agent – Project Explanation

This document explains the setup, structure, and progress of the Legal Law Firm Agent project.
It is written in a README-style format so that any new contributor or teammate can quickly
understand what has been built and how to continue the work.

---

## 1. Project Goal

The goal of this project is to build an AI-powered **Legal Law Firm Agent** that can:

* Answer legal questions in a lawyer-like manner.
* Summarize long legal cases and documents.
* Suggest relevant legal clauses for contracts.
* Help lawyers and researchers quickly navigate large corpora of case law.

This is especially useful for old or complex cases where manually reading hundreds
of pages is impractical.

---

## 2. Tech Stack

The project uses a **Turborepo** monorepo setup with multiple apps:

* **Frontend** → `apps/web`
  Built using **Next.js (TypeScript)**. This will be the user-facing interface
  for asking legal questions, browsing results, and interacting with the AI agent.

* **Backend** → `apps/api`
  Built using **FastAPI (Python)**. This is the API layer that connects the
  frontend to the model and the databases.

* **Training** → `apps/training`
  This folder contains everything related to model fine-tuning, dataset preparation,
  and experiments with adapting local LLMs to the legal domain.

Additional components (to be added later):

* **Qdrant**: Vector database for semantic search / RAG.
* **Postgres**: Database for structured metadata storage.
* **Docker Compose**: For running backend + databases locally.

---

## 3. Local Model Setup

* We are using **Qwen 3 (8B parameters)** as the base model.
* It is installed locally via **Ollama**, which allows easy inference.
* For now, we are focusing on:

  1. Retrieval-Augmented Generation (RAG) with case law.
  2. Fine-tuning / domain adaptation if needed (via LoRA/QLoRA).

---

## 4. Dataset Work

We are focusing on **Indian Legal Datasets** from Kaggle.

### Example dataset used:

* **LLM Fine-tuning Dataset of Indian Legal Texts**
  Kaggle link: [https://www.kaggle.com/datasets/akshatgupta7/llm-fine-tuning-dataset-of-indian-legal-texts](https://www.kaggle.com/datasets/akshatgupta7/llm-fine-tuning-dataset-of-indian-legal-texts)
  Command used (from inside `apps/training` folder):

  ```bash
  kaggle datasets download -d akshatgupta7/llm-fine-tuning-dataset-of-indian-legal-texts -p data/legal_qa --unzip
  ```

This downloads legal QA datasets into `apps/training/data/legal_qa`.

Other potential Kaggle datasets include:

* Indian Supreme Court Judgments.
* Indian Legal Case Summaries.
* Contract clause datasets.

---

## 5. Virtual Environment Setup

We use **Poetry** or a plain Python venv for backend + training.

To activate:

```bash
cd apps/training
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\Activate      # Windows (PowerShell)
```

---

## 6. Dataset Preparation

Before fine-tuning, raw datasets must be converted into **instruction format** for LLM training:

```json
{"instruction": "Summarize this case.", "input": "FULL CASE TEXT", "output": "Brief summary."}
{"instruction": "What was the verdict?", "input": "FULL CASE TEXT", "output": "Court ruled in favor of plaintiff."}
```

We will create a script `prepare_dataset.py` to transform CSV/JSON datasets into this format and output `processed.jsonl`.

---

## 7. Fine-Tuning Plan

* Direct fine-tuning of Qwen 3 (8B) is computationally expensive.
* We will use **LoRA / QLoRA fine-tuning** on top of the base model for efficiency.
* Training will be done with Hugging Face’s `transformers`, `peft`, `accelerate`, and `trl`.

Basic stack install:

```bash
pip install transformers datasets peft accelerate bitsandbytes trl
```

Outputs (adapter weights) will be saved in:

```
apps/training/outputs/lora-legal/
```

Later, these can be merged into the base model or loaded dynamically.

---

## 8. Current Progress

* Turborepo with Next.js frontend + FastAPI backend created.
* Virtual environment set up for training.
* Kaggle CLI configured, and first dataset (`LLM Fine-tuning Dataset of Indian Legal Texts`) downloaded successfully into `apps/training/data/legal_qa`.
* Next step is preprocessing this dataset into instruction format.

---

## 9. Next Steps

1. Write `prepare_dataset.py` to clean/convert dataset into JSONL (`processed.jsonl`).
2. Test ingestion into **Qdrant** for RAG (before fine-tuning).
3. Optionally start LoRA fine-tuning on Qwen 3 with prepared dataset.
4. Connect the fine-tuned model (or RAG pipeline) to FastAPI backend.
5. Build simple frontend interface (query box + display results).

---

## 10. Folder Structure

```
LegalLawFirmAgent/
│
├── apps/
│   ├── web/               # Next.js frontend
│   ├── api/               # FastAPI backend
│   └── training/          # Datasets + fine-tuning
│       ├── data/          # Raw and processed datasets
│       ├── outputs/       # Model checkpoints / LoRA adapters
│       └── .venv/         # Virtual environment
│
└── docker-compose.yml     # (to be added later: backend + qdrant + postgres)
```

---

# Summary

The Legal Law Firm Agent project is a monorepo with frontend, backend, and training apps.
It is built around Qwen 3 (8B) running locally with Ollama, augmented by Kaggle-sourced
Indian legal datasets. We have downloaded our first dataset, set up the training environment,
and are preparing for dataset transformation and fine-tuning. Next steps involve
data preprocessing, RAG integration, and eventually fine-tuning.
