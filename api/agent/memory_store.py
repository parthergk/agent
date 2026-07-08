import json
import uuid
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from db import qdrant_client
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, VectorParams, Distance, PayloadSchemaType

load_dotenv()

client = OpenAI()

# Ensure the 'memories' collection exists in Qdrant and has index
try:
    collections = qdrant_client.get_collections().collections
    existing_collections = [c.name for c in collections]
    if "memories" not in existing_collections:
        qdrant_client.create_collection(
            collection_name="memories",
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE
            )
        )
        qdrant_client.create_payload_index(
            collection_name="memories",
            field_name="memory_type",
            field_schema=PayloadSchemaType.KEYWORD
        )
except Exception as e:
    print(f"Failed to check/create 'memories' collection and index: {e}")


def save_memory(memory_type: str, content: str, metadata: dict) -> str:
    """
    Saves a memory point to the 'memories' Qdrant collection.
    """
    try:
        # Create text embedding representation using memory_type, title, category, and description
        title = metadata.get("title", "")
        category = metadata.get("category", "")
        description = metadata.get("description", "")
        text_to_embed = f"Type: {memory_type}\nTitle: {title}\nCategory: {category}\nDescription: {description}"
        
        response = client.embeddings.create(
            input=text_to_embed,
            model="text-embedding-3-small"
        )
        vector = response.data[0].embedding
        
        point_id = str(uuid.uuid4())
        qdrant_client.upsert(
            collection_name="memories",
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "memory_type": memory_type,
                        "content": content,
                        "metadata": metadata
                    }
                )
            ]
        )
        return f"Successfully saved memory of type '{memory_type}'."
    except Exception as e:
        return f"Error saving memory: {str(e)}"


def search_memory(query: str, memory_type: Optional[str] = None) -> str:
    """
    Searches the 'memories' collection using vector similarity.
    """
    try:
        response = client.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_vector = response.data[0].embedding
        
        # Build keyword filter
        query_filter = None
        if memory_type:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value=memory_type)
                    )
                ]
            )
            
        try:
            search_results = qdrant_client.query_points(
                collection_name="memories",
                query=query_vector,
                query_filter=query_filter,
                limit=5
            )
            points = search_results.points
        except Exception as filter_err:
            # Fallback to post-filtering if index filter fails
            print(f"Filter query failed: {filter_err}. Retrying with post-filtering...")
            search_results = qdrant_client.query_points(
                collection_name="memories",
                query=query_vector,
                limit=20
            )
            points = search_results.points
            if memory_type:
                points = [p for p in points if p.payload.get("memory_type") == memory_type][:5]
        
        matches = []
        for point in points:
            matches.append({
                "score": point.score,
                "memory_type": point.payload.get("memory_type"),
                "content": point.payload.get("content"),
                "metadata": point.payload.get("metadata", {})
            })
            
        return json.dumps(matches)
    except Exception as e:
        return f"Error searching memory: {str(e)}"
