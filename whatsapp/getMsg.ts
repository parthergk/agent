import fs from "fs";
import path from "path";
import {
  downloadMediaMessage,
  proto,
  makeWASocket
} from "baileys";

type WASocket = ReturnType<typeof makeWASocket>;

export default async function getMsg(msg: proto.IWebMessageInfo, sock: WASocket): Promise<string | undefined> {
    if (msg.message?.conversation || msg.message?.extendedTextMessage) {
        const text =
          msg.message?.conversation ||
          msg.message?.extendedTextMessage?.text ||
          "";
          return text;
      } else if (msg.message?.imageMessage) {
        const buffer = await downloadMediaMessage(
          msg as any,
          "buffer",
          {},
          {
            logger: console as any,
            reuploadRequest: sock.updateMediaMessage,
          },
        ) as Buffer;

        const filename = `${Date.now()}.jpg`;
        const filepath = path.join("uploads", filename);
        
        // Ensure uploads directory exists
        const uploadsDir = path.dirname(filepath);
        if (!fs.existsSync(uploadsDir)) {
            fs.mkdirSync(uploadsDir, { recursive: true });
        }
        
        fs.writeFileSync(filepath, buffer);
        
        const absolutePath = path.resolve(filepath);
        const caption = msg.message.imageMessage.caption || "";
        return `[IMAGE_PATH]: ${absolutePath}\n[CAPTION]: ${caption}`;
      } 
      return undefined;
}
