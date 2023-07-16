import pymysql
import os
from fastapi import FastAPI
from pydantic import BaseModel
import configparser
import uvicorn
from typing import List, Union, Optional, Dict, Any
import re
from starlette.middleware.cors import CORSMiddleware
import os

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
    """
    제품명 검색 API
    :param prod_name:
    :return:
    """
    conn = create_conn()
    curs = conn.cursor()
    curs.execute(
        "SELECT * FROM products WHERE prod_name LIKE %s", ("%" + prod_name + "%",)
    )
    results = curs.fetchall()
    conn.close()

    if len(results) == 0:
        return {"error": f"No product found for name: {prod_name}"}

    products = []
    for row in results:
        products.append({"prod_name": row[1], "price": row[3], "url": row[4]})

    return {"products": products}


@app.get("/api/reviews/prod_name/{prod_name}")
def read_reviews(prod_name: str):
    """
    제품명으로 리뷰 검색 API
    :param prod_name:
    :return:
    """
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews WHERE prod_name = %s", (prod_name,))
    result = cursor.fetchall()

    if len(result) == 0:
        conn.close()
        return {"error": f"No product found for name: {prod_name}"}

    reviews = []
    for row in result:
        reviews.append(
            {
                "prod_id": row[1],
                "rating": row[3],
                "title": row[4],
                "context": row[5],
                "answer": row[6],
                "review_url": row[7],
            }
        )

    conn.close()
    return {"reviews": reviews}


@app.get("/api/reviews/all")
def read_reviews():
    """
    제품명으로 리뷰 검색 API
    :param prod_name:
    :return:
    """
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reviews_ver3")
    result = cursor.fetchall()

    if len(result) == 0:
        conn.close()
        return

    reviews = []
    for row in result:
        reviews.append(
            {
                "prod_id": row[1],
                "rating": row[3],
                "title": row[4],
                "context": row[5],
                "answer": row[6],
                "review_url": row[7],
            }
        )

    conn.close()
    return {"reviews": reviews}


@app.get("/api/reviews/search/prod_name/{prod_name}")
def read_reviews(prod_name: str):
    """
    제품명으로 리뷰 검색 API (LIKE)
    :param prod_name:
    :return:
    """
    conn = create_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reviews_ver5 WHERE prod_name LIKE %s", ("%" + prod_name + "%",)
    )
    result = cursor.fetchall()

    if len(result) == 0:
        conn.close()
        return {"error": f"No product found for name: {prod_name}"}

    reviews = []
    for row in result:
        reviews.append(
            {
                "prod_id": row[1],
                "prod_name": row[2],
                "rating": row[3],
                "title": row[4],
                "context": row[5],
                "answer": row[6],
                "review_url": row[7],
            }
        )

    conn.close()

    # return {"reviews": dict_to_list(reviews)}
    return {"reviews": reviews}


@app.get("/api/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
