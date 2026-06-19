from qdrant_client import QdrantClient;
from qdrant_client.models import Distance, VectorParams

qdrant_client  = QdrantClient(
    host="localhost",
    port=6333
)

qdrant_client.create_collection(
    collection_name="links",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
    )
)