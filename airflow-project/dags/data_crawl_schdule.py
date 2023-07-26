from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime
import pandas as pd
import requests
import json
import csv
import logging
from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
import time

def connect_to_mysql_and_crawl_data_and_insert_summary():
    # 1. MySQL로부터 데이터를 가져옴
    hook = MySqlHook(mysql_conn_id='salmon_airflow_serving', charset='utf8mb4')
    connection = hook.get_conn()
    cursor = connection.cursor()
    cursor.execute("SELECT todo_search_product_id, search_name, crawl_yn from todo_search_products where crawl_yn = 'N' limit 1")  # SQL query
    results = cursor.fetchall()
    print(results[0])

    with open("dags/go.csv", "w", encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(results)
        f.flush()

    # 2. FastAPI를 통해 리뷰의 요약을 생성
    for result in results:
        if result[1] is None or result[1] == '' or result[1] == ' ':
            continue

        headers = {'Content-Type': 'application/json'}
        requests.get("http://49.50.166.224:30008/api/crawl/"+result[1], headers=headers)
        time.sleep(3)

        cursor.execute("UPDATE todo_search_products SET crawl_yn = 'Y' WHERE todo_search_product_id = %s", (result[0],))
        connection.commit()

    # 커넥션을 닫음
    cursor.close()
    connection.close()



dag = DAG(
    'crawl_data',
    start_date=days_ago(2),  # DAG 정의 기준 2일 전부터 시작합니다
    schedule_interval='0 5 * * *',  # 새벽 5시 스케쥴
    tags=["crawl_data"],
)

task = PythonOperator(
    task_id='connect_to_mysql_and_crawl_data_and_insert_summary',
    python_callable=connect_to_mysql_and_crawl_data_and_insert_summary,
    dag=dag,
)

