from db import qdrant_client;
from qdrant_client.models import VectorParams, Distance

qdrant_client.create_collection(
    collection_name="links",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
    )
)