import os
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

def save_uploaded_file_if_configured(uploaded_file):
    account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "uploads")
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    if not account_url and not connection_string:
        return None

    uploaded_file.seek(0)
    blob_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uploaded_file.name}"

    if connection_string:
        client = BlobServiceClient.from_connection_string(connection_string)
    else:
        client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())

    container = client.get_container_client(container_name)
    try:
        container.create_container()
    except Exception:
        pass

    blob = container.get_blob_client(blob_name)
    blob.upload_blob(uploaded_file.read(), overwrite=True)
    uploaded_file.seek(0)
    return blob.url
