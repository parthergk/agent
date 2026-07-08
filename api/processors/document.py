import os
from typing import Optional
from agent import IncomingMessage

# Import other processors for routing when a media file is sent as a document
from .image import process_image
from .audio import process_audio
from .video import process_video

def process_document(path: Optional[str], caption: Optional[str], mime_type: Optional[str]) -> IncomingMessage:
    if not path:
        return IncomingMessage(
            type="document",
            path=path,
            caption=caption or "[Document: No file path provided]",
            mime_type=mime_type
        )

    # 1. Determine type by MIME-type and file extension
    ext = os.path.splitext(path)[1].lower()
    mime = mime_type.lower() if mime_type else ""

    # 2. Check if the document is actually an Image (e.g. image/png, image/jpeg, etc.)
    if mime.startswith("image/") or ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}:
        return process_image(path, caption, mime_type)

    # 3. Check if the document is actually an Audio file (e.g. audio/mpeg, audio/ogg, etc.)
    elif mime.startswith("audio/") or ext in {".mp3", ".ogg", ".wav", ".m4a", ".aac", ".amr", ".opus"}:
        return process_audio(path, mime_type)

    # 4. Check if the document is actually a Video (e.g. video/mp4, video/quicktime, etc.)
    elif mime.startswith("video/") or ext in {".mp4", ".mov", ".avi", ".mkv", ".3gp", ".webm"}:
        return process_video(path, caption, mime_type)

    # 5. Handle Text-based Documents directly
    elif ext in {".txt", ".md", ".json", ".xml", ".csv", ".ini", ".yaml", ".yml", ".py", ".js", ".ts", ".html", ".css"}:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content_text = f.read()
            filename = os.path.basename(path)
            return IncomingMessage(
                type="document",
                path=path,
                caption=caption or f"Here is the content of the document ({filename}):\n<document name=\"{filename}\">\n{content_text}\n</document>",
                mime_type=mime_type
            )
        except Exception as e:
            return IncomingMessage(
                type="document",
                path=path,
                caption=caption or f"[Error reading text document: {str(e)}]",
                mime_type=mime_type
            )

    # 6. Stub routing for Office files and Archives
    elif ext == ".pdf":
        return IncomingMessage(
            type="document",
            path=path,
            caption=caption or "[PDF Text Extraction Placeholder]",
            mime_type=mime_type
        )
    elif ext in {".docx", ".doc"}:
        return IncomingMessage(
            type="document",
            path=path,
            caption=caption or "[Word Document Text Extraction Placeholder]",
            mime_type=mime_type
        )
    elif ext in {".xlsx", ".xls"}:
        return IncomingMessage(
            type="document",
            path=path,
            caption=caption or "[Excel Spreadsheet Data Extraction Placeholder]",
            mime_type=mime_type
        )
    elif ext in {".zip", ".rar", ".tar", ".gz"}:
        return IncomingMessage(
            type="document",
            path=path,
            caption=caption or "[Archive Index/Structure Placeholder]",
            mime_type=mime_type
        )

    # 7. Fallback for unsupported binary formats
    filename = os.path.basename(path)
    return IncomingMessage(
        type="document",
        path=path,
        caption=caption or f"[Document: Unsupported file format ({ext}) for file {filename}]",
        mime_type=mime_type
    )
