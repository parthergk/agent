from agent import IncomingMessage
from processor.process_image import process_image
from processor.process_audio import process_audio
from processor.process_video import process_video
from processor.process_document import process_document

def preprocess_message(message: IncomingMessage) -> IncomingMessage:
    if message.type == "text":
        return message
    elif message.type == "image":
        return process_image(message.path, message.caption, message.mime_type)
    elif message.type == "audio":
        return process_audio(message.path, message.caption, message.mime_type)
    elif message.type == "video":
        return process_video(message.path, message.caption, message.mime_type)
    elif message.type == "document":
        return process_document(message.path, message.caption, message.mime_type)
    return message