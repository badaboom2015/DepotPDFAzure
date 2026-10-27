import os
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential


def save_uploaded_file_if_configured(uploaded_file):
    account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "uploads")
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    if not account_url and not connection_string:
        return None

    filename = Path(uploaded_file.name.replace("\\", "/")).name or "upload"
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    blob_name = f"{timestamp}-{uuid4().hex}-{filename}"
    uploaded_file.seek(0)
    try:
        with ExitStack() as stack:
            if connection_string:
                client = BlobServiceClient.from_connection_string(connection_string)
            else:
                credential = DefaultAzureCredential()
                stack.callback(credential.close)
                client = BlobServiceClient(account_url=account_url, credential=credential)
            stack.callback(client.close)
            container = client.get_container_client(container_name)
            try:
                container.create_container()
            except ResourceExistsError:
                pass
            blob = container.get_blob_client(blob_name)
            blob.upload_blob(uploaded_file.read(), overwrite=False)
            return blob.url
    finally:
        uploaded_file.seek(0)
