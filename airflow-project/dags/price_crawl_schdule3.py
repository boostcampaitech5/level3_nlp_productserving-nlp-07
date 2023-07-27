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
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup as bs
from pathlib import Path
from typing import Optional,Union,Dict,List
import time
import os
import re
import requests as rq
import json
import csv
from datetime import datetime
from tqdm import tqdm
import sys



def get_headers(
    key: str,
    default_value: Optional[str] = None
    )-> Dict[str,Dict[str,str]]:


    """ Get Headers """
    # JSON_FILE : str = './json/headers.json'
    JSON_FILE = Path(__file__).resolve().parent / 'json' / 'headers.json'

    with open(JSON_FILE,'r',encoding='UTF-8') as file:
        headers : Dict[str,Dict[str,str]] = json.loads(file.read())

    try :
        return headers[key]
    except:
        if default_value:
            return default_value
        raise EnvironmentError(f'Set the {key}')
    
def extract_price(url):
    __headers = get_headers(key='headers')
    __headers['referer'] = url 

    # Send a request to the website
    r = requests.get(url, headers=__headers)
    # Parse the HTML document
    soup = BeautifulSoup(r.text, 'html.parser')

    # Assuming price is under a HTML tag with id 'price'
    price = soup.find(class_='total-price').text
    price = re.sub('[^0-9]', '', price)
    price = int(price.replace(',', ''))

    return price


def connect_to_mysql_and_crawl_price_data():

    # 1. MySQL로부터 데이터를 가져옴
    hook = MySqlHook(mysql_conn_id='salmon_airflow_serving', charset='utf8mb4')
    connection = hook.get_conn()
    cursor = connection.cursor()
    cursor.execute("SELECT product_id, url from products_ver100 limit 1")  # SQL query
    results = cursor.fetchall()
    print(results[0])

    with open("dags/price_crawl.csv", "w", encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(results)
        f.flush()

    # 2. FastAPI를 통해 리뷰의 요약을 생성
    for result in results:
        if result[1] is None or result[1] == '' or result[1] == ' ':
            continue

        params = {'url': result[1]}
        print(params)
        price = extract_price("https://www.coupang.com/vp/products/166996432?itemId=478240933&vendorItemId=4200250100&pickType=COU_PICK")
        print("price: ", price)
        print("result[0]: ", result[0])
        cursor.execute("UPDATE products_ver100 SET price = %s WHERE product_id = %s", (str(price), result[0]))
        connection.commit()

        time.sleep(3)

    # 커넥션을 닫음
    cursor.close()
    connection.close()



dag = DAG(
    'price_crawl_schdule3',
    start_date=days_ago(2),  # DAG 정의 기준 2일 전부터 시작합니다
    schedule_interval='0 6 * * *',  # 새벽 5시 스케쥴
    tags=["price_crawl_schdule3"],
)

task = PythonOperator(
    task_id='connect_to_mysql_and_crawl_price_data',
    python_callable=connect_to_mysql_and_crawl_price_data,
    dag=dag,
)

