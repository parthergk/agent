from typing import Optional
from agent import IncomingMessage

def process_image(path: Optional[str], caption: Optional[str], mime_type: Optional[str]) -> IncomingMessage:
    # This is a stub function for image processing logic.
    return IncomingMessage(
        type="image",
        path=path,
        caption=caption,
        mime_type=mime_type
    )
