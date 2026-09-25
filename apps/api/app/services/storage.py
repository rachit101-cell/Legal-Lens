"""
LegalLens API — Local Object Storage Service.

Handles secure file storage and retrieval using S3-compatible backend (MinIO).
"""

from __future__ import annotations

import io
from datetime import timedelta
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class StorageService:
    """Service for interacting with MinIO/S3 object storage."""

    def __init__(self) -> None:
        """Initialize the storage service with settings."""
        self.settings = get_settings()
        
        self.bucket = self.settings.object_storage_bucket
        
        # Configure Boto3 client for MinIO / S3 / Supabase
        self.client = boto3.client(
            "s3",
            endpoint_url=self.settings.object_storage_endpoint,
            aws_access_key_id=self.settings.object_storage_access_key,
            aws_secret_access_key=self.settings.object_storage_secret_key,
            config=Config(signature_version="s3v4"),
            region_name=self.settings.object_storage_region,
        )
        
        # Ensure bucket exists
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Ensure the private storage bucket exists."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = str(e.response.get("Error", {}).get("Code", ""))
            if error_code in ("404", "NoSuchBucket"):
                logger.info("creating_storage_bucket", bucket=self.bucket)
                try:
                    if self.settings.object_storage_region == "us-east-1":
                        self.client.create_bucket(Bucket=self.bucket)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket,
                            CreateBucketConfiguration={"LocationConstraint": self.settings.object_storage_region},
                        )
                except Exception as create_err:
                    logger.warning("could_not_create_bucket_automatically", error=str(create_err))
            elif error_code in ("403", "AccessDenied"):
                logger.info("bucket_head_access_restricted_continuing", bucket=self.bucket)
            else:
                logger.warning("storage_bucket_check_warning", error=str(e))

    def put_private(
        self,
        object_name: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Store a private object in the bucket.
        
        Returns the object name (key).
        """
        if isinstance(data, bytes):
            data = io.BytesIO(data)
            
        try:
            self.client.upload_fileobj(
                data,
                self.bucket,
                object_name,
                ExtraArgs={"ContentType": content_type},
            )
            return object_name
        except ClientError as e:
            logger.error("storage_upload_failed", object_name=object_name, error=str(e))
            raise

    def get_private(self, object_name: str) -> bytes:
        """
        Retrieve a private object from the bucket as bytes.
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_name)
            return response["Body"].read()  # type: ignore[no-any-return]
        except ClientError as e:
            logger.error("storage_download_failed", object_name=object_name, error=str(e))
            raise

    def delete(self, object_name: str) -> None:
        """
        Delete an object from the bucket.
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_name)
        except ClientError as e:
            logger.error("storage_delete_failed", object_name=object_name, error=str(e))
            raise

    def generate_presigned_url(
        self,
        object_name: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a pre-signed URL to share private objects temporarily.
        """
        try:
            return self.client.generate_presigned_url(  # type: ignore[no-any-return]
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_name},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logger.error(
                "storage_presigned_url_failed",
                object_name=object_name,
                error=str(e),
            )
            raise


# Singleton instance
storage_service = StorageService()
