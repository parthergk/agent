import fs from "fs";
import path from "path";
import { downloadMediaMessage, proto, makeWASocket } from "baileys";

type WASocket = ReturnType<typeof makeWASocket>;

export async function saveMedia(
  msg: proto.IWebMessageInfo,
  sock: WASocket,
  extension: string
): Promise<string> {
  const buffer = await downloadMediaMessage(
    msg as any,
    "buffer",
    {},
    {
      logger: console as any,
      reuploadRequest: sock.updateMediaMessage,
    }
  ) as Buffer;

  const filename = `${Date.now()}.${extension}`;

  const filepath = path.join("uploads", filename);

  fs.mkdirSync("uploads", { recursive: true });

  fs.writeFileSync(filepath, buffer);

  return path.resolve(filepath);
}
