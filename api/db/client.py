import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()

QDRANT_API_KEY = os.getenv("API_KEY")

qdrant_client = QdrantClient(
    url="https://30cc1a50-8f9f-487c-9199-47283e4785df.eu-west-1-0.aws.cloud.qdrant.io",
    api_key=QDRANT_API_KEY,
    cloud_inference=True
)
