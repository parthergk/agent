TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Store a user memory (link, image, audio, video, or document) in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "memory_type": {
                        "type": "string",
                        "enum": ["link", "image", "audio", "video", "document"],
                        "description": "The classification of the memory."
                    },
                    "content": {
                        "type": "string",
                        "description": "For file types (image, audio, video, document), use the file path. For link type, use the URL."
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Information parsed/generated from the caption, e.g. title, category, and description.",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "A generated title for the memory based on the caption/description."
                            },
                            "category": {
                                "type": "string",
                                "description": "A generated category name for categorization."
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the memory."
                            }
                        },
                        "required": ["title", "category", "description"]
                    }
                },
                "required": ["memory_type", "content", "metadata"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Query stored memories semantically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The text to search for within memories."
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["link", "image", "audio", "video", "document"],
                        "description": "Optional type parameter to restrict the search filter."
                    }
                },
                "required": ["query"]
            }
        }
    }
]
