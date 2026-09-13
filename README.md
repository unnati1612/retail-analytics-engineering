# Retail Analytics & Customer 360 Data Platform

> An end-to-end retail analytics engineering project that combines historical e-commerce data with simulated daily API data and turns it into tested, analytics-ready datasets and Tableau dashboards.

![Python](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![BigQuery](https://img.shields.io/badge/Warehouse-BigQuery-4285F4?logo=googlecloud&logoColor=white)
![dbt](https://img.shields.io/badge/Transform-dbt-orange?logo=dbt&logoColor=white)
![Airflow](https://img.shields.io/badge/Orchestration-Airflow-017CEE?logo=apacheairflow&logoColor=white)
![Docker](https://img.shields.io/badge/Runtime-Docker-2496ED?logo=docker&logoColor=white)
![Tableau](https://img.shields.io/badge/BI-Tableau-E97627?logo=tableau&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

## Overview

This project demonstrates a production-style **analytics engineering pipeline for e-commerce**.

The historical foundation is the **Olist Brazilian E-Commerce Public Dataset**. A custom **FastAPI + SQLite** application then simulates new and updated retail data so the platform can demonstrate incremental ingestion instead of stopping at a one-time CSV load.

The pipeline:

1. Loads historical source data into BigQuery.
2. Generates simulated daily activity through the API.
3. Extracts only new/updated records using entity-level watermarks.
4. Appends API data to BigQuery ingestion tables with batch metadata.
5. Combines and deduplicates data in dbt.
6. Builds reusable facts, dimensions, customer analytics, and executive KPIs.
7. Runs data-quality tests and ingestion validation.
8. Orchestrates the workflow with Airflow.
9. Publishes the analytics layer to Tableau.
10. Validates code and the dbt project through GitHub Actions.

The result is a complete flow from **source system → warehouse → transformation → quality checks → orchestration → BI**.

---

## 📌 Architecture Overview

                         ┌────────────────────────────┐
                         │ Olist Historical Dataset   │
                         │       CSV Files            │
                         └─────────────┬──────────────┘
                                       │
                                       ▼
                         ┌────────────────────────────┐
                         │     BigQuery Raw Layer     │
                         │       retail_raw           │
                         └─────────────┬──────────────┘
                                       │
                                       │
                  ┌────────────────────┴────────────────────┐
                  │                                         │
                  ▼                                         ▼
       ┌──────────────────────┐                 ┌──────────────────────┐
       │ Synthetic E-commerce │                 │ Incremental Python   │
       │ FastAPI + SQLite     │                 │ Ingestion Framework  │
       └──────────┬───────────┘                 └──────────┬───────────┘
                  │                                        │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────────┐
                         │ Append-only Ingestion      │
                         │ _ingest_* Tables           │
                         │                            │
                         │ batch_id                   │
                         │ ingested_at                │
                         │ record_hash                │
                         └─────────────┬──────────────┘
                                       │
                                       ▼
                         ┌────────────────────────────┐
                         │       dbt Staging          │
                         │ Cleaning + Deduplication   │
                         └─────────────┬──────────────┘
                                       │
                                       ▼
                         ┌────────────────────────────┐
                         │     dbt Intermediate       │
                         │ Business Transformations   │
                         └─────────────┬──────────────┘
                                       │
                                       ▼
                         ┌────────────────────────────┐
                         │       dbt Marts            │
                         │ Facts + Dimensions + KPIs  │
                         └─────────────┬──────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         │                           │
                         ▼                           ▼
                ┌───────────────────┐      ┌────────────────────┐
                │     Tableau       │      │ Data Quality &     │
                │    Dashboards     │      │ Monitoring         │
                └───────────────────┘      └────────────────────┘


                         ┌───────────────────┐
                         │ Apache Airflow    │
                         │ Orchestration     │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         End-to-End Pipeline


                         ┌───────────────────┐
                         │ GitHub Actions    │
                         │ CI / Validation   │
                         └───────────────────┘

### Main technologies

| Layer | Technology |
|---|---|
| Source simulation | FastAPI + SQLite |
| Historical source | Olist dataset |
| Ingestion | Python |
| Warehouse | Google BigQuery |
| Transformation | dbt |
| Orchestration | Apache Airflow |
| Runtime | Docker / Docker Compose |
| BI | Tableau |
| CI/CD | GitHub Actions |
| Cloud authentication | GCP Workload Identity Federation |

---

## Source & Incremental Ingestion

### Synthetic API

The `source_api/` application exposes:

```text
/customers
/products
/sellers
/orders
/order-items
/payments
/reviews
/source/status
/health
```

The source supports timestamp-based extraction such as `updated_after` for master entities and `created_after` for transactional entities.

This allows the project to simulate a source that changes every day.

### Watermark-based ingestion

Watermarks are stored in `ingestion/watermarks.json`.

The ingestion flow is:

```text
Read previous watermark
        ↓
Request records after watermark
        ↓
Paginate through API results
        ↓
Append to BigQuery
        ↓
Validate load
        ↓
Advance watermark only on success
```

A failed batch therefore does not incorrectly move the extraction point forward.

### Append-only design

Incremental API data is written to:

```text
retail_raw._ingest_customers
retail_raw._ingest_products
retail_raw._ingest_sellers
retail_raw._ingest_orders
retail_raw._ingest_order_items
retail_raw._ingest_payments
retail_raw._ingest_reviews
```

Each ingestion record can carry:

```text
_ingested_at
_batch_id
_record_hash
```

The raw layer stays append-only; current-state deduplication happens downstream in dbt.

This design is especially useful in the **BigQuery Sandbox**, where DML operations such as `MERGE`, `UPDATE`, and `DELETE` are not available.

### Retry safety & deduplication

Business keys are used to identify the logical record:

```text
customers   → customer_id
products    → product_id
sellers     → seller_id
orders      → order_id
order_items → order_id + order_item_id
payments    → order_id + payment_sequential
reviews     → review_id + order_id
```

If a batch is retried, the append-only raw layer can contain the repeated ingestion, while dbt selects the appropriate record for the analytics layer.

---

## BigQuery Model

Three logical datasets are used:

```text
retail_raw
retail_staging
retail_analytics
```

### Raw

Historical source tables plus append-only `_ingest_*` tables.

### Staging

Standardized and deduplicated representations of the source entities.

### Analytics

Business-ready facts, dimensions, and marts consumed by Tableau.

---

## dbt Transformation Layer

The dbt project follows a staging → intermediate → marts structure.

```text
dbt/retail_analytics/
├── models/
│   ├── staging/
│   ├── intermediate/
│   └── marts/
├── macros/
├── snapshots/
└── dbt_project.yml
```

### Core analytical models

**Facts**

```text
fct_orders
fct_order_items
```

**Dimensions**

```text
dim_customers
dim_products
dim_sellers
```

**Marts**

```text
mart_daily_sales
mart_executive_kpis
mart_customer_rfm
mart_ingestion_monitoring
```

The transformation layer is where source data becomes business meaning. Examples include order enrichment, delivery calculations, customer RFM metrics, seller performance, daily sales, and executive KPI calculations.

---

## Customer 360 & RFM

`mart_customer_rfm` combines customer purchase behavior into:

- **Recency** – how recently the customer purchased
- **Frequency** – how often the customer purchased
- **Monetary** – how much value the customer generated

Segments include:

```text
Champions
Loyal Customers
Potential Loyalists
New Customers
At Risk
Hibernating
```

This supports customer value analysis, repeat-purchase analysis, and retention-oriented reporting.

---

## Executive KPI Definitions

The project intentionally keeps different monetary concepts separate:

- **Item value / sales** = merchandise value used as the primary sales metric.
- **Freight value** = shipping value.
- **Recorded payment value** = payment amount actually present in the source.

Core KPIs include:

```text
Total Orders
Total Sales
Average Order Value
Customers
Repeat Customer Rate
Average Delivery Days
Late Delivery Rate
Payment Coverage
```

This avoids silently mixing revenue, shipping, and recorded payment amounts into one metric.

---

## Data Quality

Data quality is implemented with dbt tests and pipeline validation.

Checks include:

- Uniqueness
- Not-null constraints
- Referential integrity
- Composite-key uniqueness
- Valid ingestion statuses/results
- Ingestion record counts
- Ingestion duration

### Deliberate anomaly handling

One delivered historical order has **no recorded payment**. The project does not invent a payment value to make the data look clean. Instead, the anomaly is retained and surfaced as a **dbt warning/data-quality note**.

This is an important design principle: **preserve source truth, then expose exceptions clearly**.

---

## Ingestion Audit & Monitoring

Each batch records operational information such as:

```text
batch_id
entity
records_fetched
records_loaded
started_at
completed_at
duration_seconds
status
ingestion_result
```

This makes it possible to answer questions such as:

- Did the batch run?
- Did it return data?
- How many rows were loaded?
- How long did it take?
- Which entity failed?

---

## Airflow Orchestration

The main DAG is:

```text
retail_analytics_pipeline
```

Its workflow is:

```text
generate_batch_id
        ↓
simulate_new_day
        ↓
generate_reviews
        ↓
ingest_api_data
        ↓
dbt_run
        ↓
dbt_test
        ↓
validate_ingestion
```

The DAG is scheduled for daily execution using the `Asia/Kolkata` timezone.

Airflow runs in Docker alongside the source API and PostgreSQL metadata database.

---

## Tableau Dashboards

The analytics layer powers four connected Tableau dashboards.

### 1. Retail Executive Overview

High-level business view containing:

- Total Sales
- Orders
- Average Order Value
- Customers
- Repeat Customer Rate
- Payment Coverage
- Sales Trend
- Orders Trend
- Data-quality note

### 2. Customer Analytics

Contains:

- Customer Segments
- Revenue by Segment
- One-time vs Repeat Customers
- RFM Customer Value

A customer-segment filter can be applied across the dashboard.

### 3. Operations & Delivery

Contains:

- Average Delivery Days
- Late Delivery Rate
- Delivered Orders
- Actual vs Estimated Delivery Time
- Orders by Status
- Late Deliveries Over Time

### 4. Product & Seller Performance

Contains:

- Top Products by Revenue
- Top Products by Units Sold
- Top Sellers by Revenue
- Seller Delivery Performance

Product category and seller-performance analysis are supported through dashboard filters and interactions.

The dashboards are connected using navigation buttons so users can move between executive, customer, operational, and product/seller views.

---

## Current Results

The final analytics layer contains approximately:

| Metric | Result |
|---|---:|
| Orders | 100K+ |
| Customers | 96K+ |
| Sales | ₹15M+ |
| Average Order Value | ₹150+ |
| Payment Coverage | 99.999% |
| Repeat Customer Rate | ~4% |

The numbers above are used as the business-facing snapshot represented by the completed Tableau dashboards.

---

## Project Structure

```text
retail-analytics-engineering/
├── ingestion/
│   ├── api_client.py
│   ├── watermark.py
│   ├── bigquery_loader.py
│   ├── load_api_data.py
│   ├── initialize_watermarks.py
│   ├── validate_ingestion.py
│   └── watermarks.json
│
├── source_api/
│   ├── main.py
│   ├── simulate_day.py
│   ├── generate_reviews.py
│   └── ...
│
├── dbt/
│   └── retail_analytics/
│       ├── models/
│       │   ├── staging/
│       │   ├── intermediate/
│       │   └── marts/
│       ├── tests/
│       ├── macros/
│       ├── snapshots/
│       └── dbt_project.yml
│
├── airflow/
│   └── dags/
├── dashboard/
├── sql/
├── data/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Running the Project

### Prerequisites

- Python 3.13+
- Docker Desktop
- Google Cloud / BigQuery access
- dbt
- Tableau Desktop
- Git

### 1. Clone

```bash
git clone https://github.com/unnati1612/retail-analytics-engineering.git
cd retail-analytics-engineering
```

### 2. Create the Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `.env` with the required BigQuery, Airflow, and API configuration.

**Do not commit credentials, service-account keys, or secrets.**

### 4. Start Docker services

```bash
docker compose up -d
```

### 5. Run incremental ingestion manually

```bash
python ingestion/load_api_data.py
```

### 6. Run dbt

From `dbt/retail_analytics/`:

```bash
dbt run
dbt test
dbt docs generate
dbt docs serve
```

### 7. Open Airflow

Use the local Airflow web interface and trigger `retail_analytics_pipeline` to run the complete workflow.

### 8. Connect Tableau

Connect Tableau Desktop to the `retail_analytics` BigQuery dataset and use the analytical marts listed above as dashboard sources.

---

## CI/CD

GitHub Actions validates repository changes with automated checks including:

- Python syntax validation
- dbt project validation
- Dependency installation
- Google Cloud authentication through **Workload Identity Federation**

The project avoids storing long-lived GCP service-account keys in GitHub.

---

## Key Engineering Decisions

### Why a synthetic API?

A static dataset cannot demonstrate incremental ingestion. The API simulates a changing operational source and makes watermarking, retries, late-arriving data, and recurring pipeline runs observable.

### Why append-only ingestion?

It preserves raw ingestion history and works within BigQuery Sandbox constraints. Deduplication is intentionally handled downstream instead of mutating raw data.

### Why dbt?

Business transformations, tests, documentation, and lineage are easier to manage when they are version-controlled and separated from ingestion code.

### Why Airflow?

The pipeline contains dependencies between simulation, ingestion, transformation, testing, and validation. Airflow makes those dependencies explicit and schedulable.

### Why Tableau?

The final models are designed for business consumption, so Tableau provides an interactive layer for executive, customer, operational, product, and seller analysis.

---

## What This Project Demonstrates

This project brings together practical examples of:

- Python data ingestion
- REST API integration
- Incremental loading
- Watermark management
- Append-only ingestion
- Retry-safe processing
- Deduplication
- BigQuery data warehousing
- dbt modeling
- Fact/dimension design
- Customer 360 and RFM analysis
- Data quality testing
- Audit logging
- Airflow orchestration
- Dockerized workflows
- Tableau dashboard development
- GitHub Actions CI/CD
- Secure cloud authentication

---

## Future Enhancements

Potential next steps for a production-scale version would include:

- BigQuery partitioning and clustering
- Streaming / near-real-time ingestion
- Data freshness monitoring and alerting
- Automated anomaly detection
- Automated Tableau refreshes
- Terraform-based infrastructure
- Cloud Composer deployment
- Customer lifetime value and churn models
- Demand forecasting

---

## Author

**Unnati Jain**  
Data & Analytics | Audit & Assurance

GitHub: [unnati1612](https://github.com/unnati1612)

---

## License / Dataset Note

The historical component uses the **Olist Brazilian E-Commerce Public Dataset**. Refer to the dataset's original terms and attribution requirements when redistributing or publishing the underlying data.
