import pymysql
import os
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from typing import List, Union, Optional, Dict, Any
import re
from starlette.middleware.cors import CORSMiddleware
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from crawler.crawling_products_bs4 import crawling_products
from crawler.crawling_reviews import CSV
from db_scripts.csv2db import run_pipeline
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import JSONResponse
import numpy as np
from dotenv import load_dotenv
load_dotenv()  # .env 파일의 내용을 읽어서 환경변수로 설정
import requests
from typing import Optional




app = FastAPI()

origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Product(BaseModel):
    prod_name: str
    price: float
    url: str


class Review(BaseModel):
    prod_name: str
    prod_id: int
    rating: float
    title: str
    context: str
    answer: str
    review_url: str


# 환경 설정
env = os.getenv("MY_APP_ENV", "local")  # 기본값은 'local'


def dict_to_list(reviews):
    reviews = [review["context"] for review in reviews]
    reviews = [re.sub(r"<[^>]+>\s+(?=<)|<[^>]+>", "", text) for text in reviews]
    reviews = [re.sub(r"[^가-힣a-zA-Z0-9\n\s]", "", text).strip() for text in reviews]

    filtered_reviews = []
    for i in range(10):
        filtered_reviews.append(" ".join(reviews[i * 20 : i * 20 + 20]))

    return filtered_reviews


# MySQL 연결 설정
def create_conn():
    print(os.getenv("MYSQL_HOST"))
    print(os.getenv("MYSQL_USER"))
    print(os.getenv("MYSQL_PASSWORD"))
    print(os.getenv("MYSQL_DB"))
    print(os.getenv("MYSQL_CHARSET"))

    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        db=os.getenv("MYSQL_DB"),
        charset=os.getenv("MYSQL_CHARSET"),
    )


@app.get("/api/product/prod_name/{prod_name}")
async def search_product(prod_name: str):
    '''
    제품명 검색 API (LIKE)
    :param prod_name:
    :return:
    '''
    conn = create_conn()
    curs = conn.cursor()
    curs.execute("SELECT product_id \
                    ,unique_product_id \
                    ,top_cnt \
                    ,search_name \
                    ,prod_name \
                    ,price \
                    ,url \
                    ,avg_rating \
                    ,review_cnt \
                    ,ad_yn \
                    ,product_img_url \
                 FROM products_ver31 WHERE prod_name LIKE %s", ('%' + prod_name + '%',))
    results = curs.fetchall()
    conn.close()

    if len(results) == 0:
        return {"error": f"No product found for name: {prod_name}"}

    products = []
    for row in results:
        # search_name,unique_product_id,top_cnt,name,price,review_cnt,rating,ad_yn,URL,product_img_url
        products.append({
            "product_id": row[0],
            "unique_product_id": row[1],
            "top_cnt": row[2],
            "search_name": row[3],
            "prod_name": row[4],
            "price": row[5],
            "url": row[6],
            "avg_rating": row[7],
            "review_cnt": row[8],
            "ad_yn": row[9],
            "product_img_url": row[10]
        })


    return {"products": products}


@app.get("/api/reviews/prod_name/{prod_name}")
def read_reviews(prod_name: str):
    '''
    정확히 일치하는 제품명 관련 리뷰 찾기 API (일치)
    :param prod_name:
    :return:
    '''
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews_ver31 WHERE prod_name = %s", (prod_name,))
    result = cursor.fetchall()

    if len(result) == 0:
        print("No review found for name: ", prod_name)
        # 크롤링 로직
        # 직접 넣도 싶다면 다음과 같은 형식으로 넣으면 된다.
        print(prod_name)
        search_list = {'음식': [prod_name]}


        product_file_name = crawling_products(search_list)

        review_file_name = CSV.save_file(product_file_name, 3)

        version = 'ver31'

        current_directory = Path(__file__).resolve().parent.parent.parent
        print(current_directory)

        product_csv_path = current_directory.joinpath("backend", "app", f"{product_file_name}.csv")
        review_csv_path = current_directory.joinpath("backend", "app", f"{review_file_name}.csv")

        product_csv_file = f"{product_csv_path}"
        review_csv_file = f"{review_csv_path}"

        run_pipeline(product_csv_file, review_csv_file, version)

        # print csv filenames
        print(os.path.basename(product_csv_file))
        print(os.path.basename(review_csv_file))

        cursor.execute("SELECT * FROM reviews_ver31 WHERE prod_name = %s", (prod_name,))
        result = cursor.fetchall()
        print("result", result)


        # product_df = pd.read_csv(product_csv_file)
        # product_df = product_df.replace([np.inf, -np.inf], np.nan)  # replace all inf by NaN
        # product_df = product_df.dropna()  # drop all rows with NaN

        # review_df = pd.read_csv(review_csv_file, dtype={"headline": str})
        # review_df = review_df.replace([np.inf, -np.inf], np.nan)  # replace all inf by NaN
        # review_df = review_df.dropna()  # drop all rows with NaN


        # products = []
        # for index, row in product_df.iterrows():
        #     products.append({
        #             "search_name": row[0], # 검색어
        #             "unique_product_id": row[1], # 쿠팡 상품 고유 ID
        #             "top_cnt": row[2], # 쿠팡 랭킹
        #             "prod_name": row[3],
        #             "price": row[4], # 가격
        #             "review_cnt": row[5], # 리뷰 수
        #             "rating": row[6], # 평균 평점
        #             "ad_yn": row[7], # 광고 여부
        #             "URL": row[8], # 상품 URL
        #             "product_img_url" : row[9] # 상품 이미지 URL
        #         })



        # reviews = []
        # for index, row in review_df.iterrows():
        #     reviews.append({
        #         "prod_name" : row[0],
        #         "rating": row[2],
        #         "title": row[3],
        #         "context": row[4],
        #         "answer": row[5]
        #     })  

        reviews = []

        for row in result:
            reviews.append({
                "prod_id": row[1],
                "prod_name" : row[2],
                "rating": row[3],
                "title": row[4],
                "context": row[5],
                "answer": row[6],
                "review_url": row[7]
            })
        


        conn.close()
        return {"source":"crawl", "reviews":reviews}

    reviews = []
    for row in result:
        reviews.append({
            "prod_id": row[1],
            "prod_name" : row[2],
            "rating": row[3],
            "title": row[4],
            "context": row[5],
            "answer": row[6],
            "review_url": row[7]
        })

    conn.close()
    return {"source":"db", "reviews": reviews}


@app.get("/api/reviews/search/prod_name/{prod_name}")
def read_reviews(prod_name: str):
    '''
    제품명으로 리뷰 검색 API (LIKE)
    :param prod_name:
    :return:
    '''
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews_ver31 WHERE prod_name LIKE %s", ('%' + prod_name + '%',))
    result = cursor.fetchall()


    if len(result) == 0:
        print("No review found for name: ", prod_name)
        # 크롤링 로직
        # 직접 넣도 싶다면 다음과 같은 형식으로 넣으면 된다.
        print(prod_name)
        search_list = {'음식': [prod_name]}


        product_file_name = crawling_products(search_list)

        review_file_name = CSV.save_file(product_file_name, 3)

        version = 'ver31'

        current_directory = Path(__file__).resolve().parent.parent.parent
        print(current_directory)

        product_csv_path = current_directory.joinpath("backend", "app", f"{product_file_name}.csv")
        review_csv_path = current_directory.joinpath("backend", "app", f"{review_file_name}.csv")

        product_csv_file = f"{product_csv_path}"
        review_csv_file = f"{review_csv_path}"

        run_pipeline(product_csv_file, review_csv_file, version)

        # print csv filenames
        print(os.path.basename(product_csv_file))
        print(os.path.basename(review_csv_file))
        conn.close()

        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reviews_ver31 WHERE prod_name LIKE %s", ('%' + prod_name + '%',))
        result = cursor.fetchall()
        print("result", result)


        # product_df = pd.read_csv(product_csv_file)
        # product_df = product_df.replace([np.inf, -np.inf], np.nan)  # replace all inf by NaN
        # product_df = product_df.dropna()  # drop all rows with NaN

        # review_df = pd.read_csv(review_csv_file, dtype={"headline": str})
        # review_df = review_df.replace([np.inf, -np.inf], np.nan)  # replace all inf by NaN
        # review_df = review_df.dropna()  # drop all rows with NaN


        # products = []
        # for index, row in product_df.iterrows():
        #     products.append({
        #             "search_name": row[0], # 검색어
        #             "unique_product_id": row[1], # 쿠팡 상품 고유 ID
        #             "top_cnt": row[2], # 쿠팡 랭킹
        #             "prod_name": row[3],
        #             "price": row[4], # 가격
        #             "review_cnt": row[5], # 리뷰 수
        #             "rating": row[6], # 평균 평점
        #             "ad_yn": row[7], # 광고 여부
        #             "URL": row[8], # 상품 URL
        #             "product_img_url" : row[9] # 상품 이미지 URL
        #         })



        # reviews = []
        # for index, row in review_df.iterrows():
        #     reviews.append({
        #         "prod_name" : row[0],
        #         "rating": row[2],
        #         "title": row[3],
        #         "context": row[4],
        #         "answer": row[5]
        #     })  

        reviews = []

        for row in result:
            reviews.append({
                "prod_id": row[1],
                "prod_name" : row[2],
                "rating": row[3],
                "title": row[4],
                "context": row[5],
                "answer": row[6],
                "review_url": row[7]
            })
        

        conn.close()
        
        return {"source":"crawl", "reviews":reviews}
    

    reviews = []
    for row in result:
        reviews.append({
            "prod_id": row[1],
            "prod_name": row[2],
            "rating": row[3],
            "title": row[4],
            "context": row[5],
            "answer": row[6],
            "review_url": row[7]
        })

    conn.close()
    return {"source":"db", "reviews": reviews}    

@app.get("/api/reviews/all")
def read_reviews():
    '''
    리뷰 전부 가져오기
    :param prod_name:
    :return:
    '''
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews_ver31")
    result = cursor.fetchall()

    if len(result) == 0:
        conn.close()
        return

    reviews = []
    for row in result:
        reviews.append({
            "prod_id": row[1],
            "prod_name": row[2],
            "rating": row[3],
            "title": row[4],
            "context": row[5],
            "answer": row[6],
            "review_url": row[7]
        })

    conn.close()
    return {"reviews": reviews}



class ProductIds(BaseModel):
    product_id: List[int]

@app.post("/api/products/url")
async def get_products(product_ids: ProductIds):
    conn = create_conn()
    cursor = conn.cursor()
    
    # SQL injection을 피하기 위해 매개변수를 안전하게 전달
    query = "SELECT product_id, url, product_img_url FROM products_ver31 WHERE product_id in ({})".format(', '.join(['%s'] * len(product_ids.product_id)))
    cursor.execute(query, tuple(product_ids.product_id))
    rows = cursor.fetchall()

    data = {}
    for row in rows:
        data["prod_id"+str(row[0])] = {  # row[0] is the product_id
            "url": row[1],  # row[1] is the url
            "product_img_url": row[2]  # row[2] is the product_img_url
        }
    
    # 데이터베이스 연결 종료
    cursor.close()
    conn.close()
    
    # code와 data를 포함한 결과 반환
    result = {"code": 200, "data": data}
    return result



class FeedbackIn(BaseModel):
    query: str
    recommendations: str
    best: Optional[str] = None
    review: Optional[str] = None


class FeedbackOut(BaseModel):
    code: int
    data: FeedbackIn




@app.post("/api/feedback/", response_model=FeedbackOut)
async def create_feedback(feedback: FeedbackIn):
    try:
        conn = create_conn()
        cursor = conn.cursor()
        cursor.execute("insert into feedback_data(query, recommendations, best, review) values(%s, %s, %s, %s)", 
                    (feedback.query, feedback.recommendations, feedback.best, feedback.review))

        # 데이터베이스 연결 종료
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        # 데이터베이스 오류 발생 시 처리
        conn.rollback()   # 이전 상태로 롤백
        raise HTTPException(status_code=500, detail="Database error")

    finally:
        # 마지막으로 항상 커서와 연결을 닫아줍니다.
        cursor.close()
        conn.close()


    try:
        return FeedbackOut(code=200, data=FeedbackIn(**feedback.dict(), feedback_id=cursor.lastrowid))
    except:
        raise HTTPException(status_code=701, detail="feedback insert Error")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)