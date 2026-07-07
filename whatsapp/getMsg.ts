import {
  proto,
  makeWASocket
} from "baileys";
import { saveMedia } from "./saveMedia.js";

type WASocket = ReturnType<typeof makeWASocket>;

export interface IncomingMessage {
  type: "text" | "image" | "audio" | "video" | "document";
  content?: string;
  path?: string;
  caption?: string;
  filename?: string;
  mime_type?: string;
}

export default async function getMsg(
  msg: proto.IWebMessageInfo,
  sock: WASocket
): Promise<IncomingMessage | undefined> {
  if (msg.message?.conversation || msg.message?.extendedTextMessage) {
    const text =
      msg.message?.conversation ||
      msg.message?.extendedTextMessage?.text ||
      "";
    return {
      type: "text",
      content: text,
    };
  } else if (msg.message?.imageMessage) {
    const img = msg.message.imageMessage;
    const mimetype = img.mimetype || "image/jpeg";
    const caption = img.caption || "";
    const extension = mimetype.split("/")[1] || "jpg";

    const absolutePath = await saveMedia(msg, sock, extension);
    return {
      type: "image",
      path: absolutePath,
      caption: caption,
      mime_type: mimetype,
    };
  } else if (msg.message?.documentMessage) {
    const doc = msg.message.documentMessage;
    const mimetype = doc.mimetype || "";
    const fileName = doc.fileName || "unknown";
    const caption = doc.caption || "";
    const extension = fileName.split(".").pop() || "bin";

    const absolutePath = await saveMedia(msg, sock, extension);
    return {
      type: "document",
      path: absolutePath,
      filename: fileName,
      mime_type: mimetype,
      caption: caption || undefined,
    };
  } else if (msg.message?.videoMessage) {
    const video = msg.message.videoMessage;
    const mimetype = video.mimetype || "video/mp4";
    const caption = video.caption || "";
    const extension = mimetype.split("/")[1] || "mp4";

    const absolutePath = await saveMedia(msg, sock, extension);
    return {
      type: "video",
      path: absolutePath,
      caption: caption,
      mime_type: mimetype,
    };
  } else if (msg.message?.audioMessage) {
    const audio = msg.message.audioMessage;
    const mimetype = audio.mimetype || "audio/mpeg";
    const extension = mimetype.split("/")[1] || "mp3";

    const absolutePath = await saveMedia(msg, sock, extension);
    return {
      type: "audio",
      path: absolutePath,
      mime_type: mimetype,
    };
  }
  return undefined;
}
