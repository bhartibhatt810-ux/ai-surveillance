import logging
from azure.storage.blob import BlobServiceClient
from config import config

logger = logging.getLogger("SurveillanceLogger")

def upload_to_azure(file_name: str, image_bytes: bytes) -> bool:
    if not config.AZURE_CONNECTION_STRING:
        logger.warning("Azure connection string not found. Skipping cloud upload.")
        return False

    try:
        blob_service_client = BlobServiceClient.from_connection_string(config.AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client("detections")
        
        if not container_client.exists():
            container_client.create_container()

        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(image_bytes, overwrite=True)
        logger.info(f"Successfully uploaded {file_name} to Azure Blob Storage.")
        return True
    except Exception as e:
        logger.error(f"Azure Blob upload failed: {e}")
        return False
