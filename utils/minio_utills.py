import json
import logging

from minio import Minio

from config.minio_config import minio_config
from processor.import_processor.base import setup_logging

setup_logging()

try:
    # 创建 MinIO 客户端
    minio_client = Minio(
        endpoint=minio_config.endpoint,
        access_key=minio_config.access_key,
        secret_key=minio_config.secret_key,
        secure=False,
    )

    # 检查存储桶（bucket）是否存在，如果不存在则创建
    if not minio_client.bucket_exists(minio_config.bucket_name):
        minio_client.make_bucket(minio_config.bucket_name)
        # 设置存储桶策略为 Public Read (只读权限开放给匿名用户)
        # 这样前端可以直接通过 URL 访问图片，而不需要预签名 URL

    # 定义当前bucket的访问权限
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{minio_config.bucket_name}/*"]
            }
        ]
    }
    # 设置当前bucket的访问权限
    minio_client.set_bucket_policy(minio_config.bucket_name, json.dumps(policy))
except Exception as e:
    logging.error(f"Minio连接，错误原因:{e}")

def get_minio_client():
    return minio_client

if __name__ == "__main__":
    get_minio_client()

