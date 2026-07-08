def preprocess_message(message):
    if(message.type == "text"):
        return message.caption
    elif(message.type == "image"):
        return process_image(message.path, message.caption, message.mime_type)
    elif(message.type == "audio"):
        return process_audio(message.path, message.caption, message.mime_type)
    elif(message.type == "video"):
        return process_video(message.path, message.caption, message.mime_type)
    elif(message.type == "document"):
        return process_document(message.path, message.caption, message.mime_type)