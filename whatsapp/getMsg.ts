import {
  proto,
  makeWASocket
} from "baileys";
import { saveMedia } from "./saveMedia.js";

type WASocket = ReturnType<typeof makeWASocket>;

export default async function getMsg(msg: proto.IWebMessageInfo, sock: WASocket): Promise<string | undefined> {
  if (msg.message?.conversation || msg.message?.extendedTextMessage) {
    const text =
      msg.message?.conversation ||
      msg.message?.extendedTextMessage?.text ||
      "";
    return text;
  } else if (msg.message?.imageMessage) {
    const img = msg.message.imageMessage;
    const mimetype = img.mimetype || "image/jpeg";
    const caption = img.caption || "";
    const extension = mimetype.split("/")[1] || "jpg";

    const absolutePath = await saveMedia(msg, sock, extension);
    return `[IMAGE_PATH]: ${absolutePath}\n[MIME_TYPE]: ${mimetype}\n[CAPTION]: ${caption}`;
  } else if (msg.message?.documentMessage) {
    const doc = msg.message.documentMessage;
    const mimetype = doc.mimetype || "";
    const fileName = doc.fileName || "unknown";
    const caption = doc.caption || "";
    const extension = fileName.split(".").pop() || "bin";

    const absolutePath = await saveMedia(msg, sock, extension);
    return `[DOCUMENT_PATH]: ${absolutePath}\n[MIME_TYPE]: ${mimetype}\n[CAPTION]: ${caption}`;
  } else if(msg.message?.videoMessage) {
    const video = msg.message.videoMessage;
    const mimetype = video.mimetype || "video/mp4";
    const caption = video.caption || "";
    const extension = mimetype.split("/")[1] || "mp4";

    const absolutePath = await saveMedia(msg, sock, extension);
    return `[VIDEO_PATH]: ${absolutePath}\n[MIME_TYPE]: ${mimetype}\n[CAPTION]: ${caption}`;
  }else if (msg.message?.audioMessage) {
    const audio = msg.message.audioMessage;
    const mimetype = audio.mimetype || "audio/mpeg";
    const extension = mimetype.split("/")[1] || "mp3";

    const absolutePath = await saveMedia(msg, sock, extension);
    return `[AUDIO_PATH]: ${absolutePath}\n[MIME_TYPE]: ${mimetype}`;
  }
  return undefined;
}
