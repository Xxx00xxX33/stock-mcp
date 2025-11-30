import asyncio
import io
import os
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from src.server.utils.logger import logger

class MinioClient:
    """Async wrapper for MinIO client."""
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9300")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET", "knowledge-base")
        self.secure = os.getenv("MINIO_SECURE", "False").lower() == "true"
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure the target bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to check/create MinIO bucket: {e}")

    async def upload_bytes(self, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload bytes to MinIO asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._upload_sync, 
            object_name, 
            data, 
            content_type
        )

    def _upload_sync(self, object_name: str, data: bytes, content_type: str) -> str:
        """Synchronous upload logic."""
        try:
            stream = io.BytesIO(data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                stream,
                length=len(data),
                content_type=content_type
            )
            # Return the s3 path or http url? 
            # Returning s3-like path is better for internal usage: s3://bucket/key
            return f"s3://{self.bucket_name}/{object_name}"
        except S3Error as e:
            logger.error(f"MinIO upload failed: {e}")
            raise e

    def get_presigned_url(self, object_name: str) -> str:
        """Get a presigned URL for downloading (optional usage)."""
        return self.client.get_presigned_url("GET", self.bucket_name, object_name)
