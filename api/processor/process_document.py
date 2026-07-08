from typing import Optional
from agent import IncomingMessage

def process_document(path: Optional[str], caption: Optional[str], mime_type: Optional[str]) -> IncomingMessage:
    # This is a stub function for document processing logic (e.g. PDF/Docx text extraction).
    return IncomingMessage(
        type="document",
        path=path,
        caption=caption,
        mime_type=mime_type,
        content="[Document Extracted Text Placeholder]"
    )
