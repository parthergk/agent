import os
import sys
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType

# Add parent directory to system path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.client import qdrant_client

# Recreate collection
try:
    qdrant_client.delete_collection(collection_name="memories")
except Exception:
    pass

qdrant_client.create_collection(
    collection_name="memories",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
    )
)

# Create keyword payload index for filtering by memory_type
qdrant_client.create_payload_index(
    collection_name="memories",
    field_name="memory_type",
    field_schema=PayloadSchemaType.KEYWORD
)
print("Database initialized successfully with memories collection and keyword index.")
