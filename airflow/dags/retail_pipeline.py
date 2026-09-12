from datetime import timedelta

import pendulum

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


local_tz = pendulum.timezone("Asia/Kolkata")

PROJECT_ROOT = "/opt/airflow/project"
DBT_DIR = f"{PROJECT_ROOT}/dbt/retail_analytics"


with DAG(
    dag_id="retail_analytics_pipeline",
    description="Incremental retail API ingestion and dbt transformation pipeline",
    start_date=pendulum.datetime(
        2026,
        1,
        1,
        tz=local_tz,
    ),
    schedule="0 23 * * *",
    catchup=False,
    tags=[
        "retail",
        "bigquery",
        "dbt",
        "analytics-engineering",
    ],
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "execution_timeout": timedelta(minutes=20),
    },
) as dag:

    generate_batch_id = BashOperator(
        task_id="generate_batch_id",
        bash_command=(
            "python -c "
            "\"from datetime import datetime, timezone; "
            "import uuid; "
            "print(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') "
            "+ '_' + uuid.uuid4().hex[:8])\""
        ),
        do_xcom_push=True,
    )

    simulate_new_day = BashOperator(
        task_id="simulate_new_day",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python source_api/simulate_day.py"
        ),
    )

    generate_reviews = BashOperator(
        task_id="generate_reviews",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python source_api/generate_reviews.py"
        ),
    )

    ingest_api_data = BashOperator(
        task_id="ingest_api_data",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python ingestion/load_api_data.py "
            "--batch-id "
            "'{{ ti.xcom_pull(task_ids=\"generate_batch_id\") }}'"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"cd {DBT_DIR} && "
            "dbt run "
            "--profiles-dir /opt/airflow/config/dbt"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {DBT_DIR} && "
            "dbt test "
            "--profiles-dir /opt/airflow/config/dbt"
        ),
    )

    validate_ingestion = BashOperator(
        task_id="validate_ingestion",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python ingestion/validate_ingestion.py "
            "--batch-id "
            "'{{ ti.xcom_pull(task_ids=\"generate_batch_id\") }}'"
        ),
    )

    (
        generate_batch_id
        >> simulate_new_day
        >> generate_reviews
        >> ingest_api_data
        >> dbt_run
        >> dbt_test
        >> validate_ingestion
    )