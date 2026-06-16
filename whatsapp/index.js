import {
    makeWASocket,
    useMultiFileAuthState
} from "baileys";

import QRCode from "qrcode";

async function askAgent(text) {
    try {
        const response = await fetch(
            "http://127.0.0.1:8000/chat",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: text
                })
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data = await response.json();

        return data.response;
    } catch (error) {
        console.error(error);

        return "Agent is currently unavailable.";
    }
}

async function connect() {
    const { state, saveCreds } =
        await useMultiFileAuthState("auth");

    const sock = makeWASocket({
        auth: state,
        shouldSyncHistoryMessage: () => false
    });

    sock.ev.on("creds.update", saveCreds);

    sock.ev.on("connection.update", async (update) => {
        const {
            connection,
            lastDisconnect,
            qr
        } = update;

        if (qr) {
            await QRCode.toFile("qr.png", qr);
            console.log("📱 Scan qr.png");
        }

        if (connection === "open") {
            console.log("✅ WhatsApp Connected");
        }

        if (connection === "close") {
            console.log("❌ Disconnected");
            console.log(lastDisconnect);

            // reconnect
            connect();
        }
    });

    sock.ev.on("messages.upsert", async ({ messages, type }) => {
        try {
            if (type !== "notify") return;

            const msg = messages?.[0];

            if (!msg) return;
            if (!msg.message) return;

            // ONLY process messages sent by YOU
            if (!msg.key.fromMe) return;

            const text =
                msg.message?.conversation ||
                msg.message?.extendedTextMessage?.text ||
                "";

            if (!text.trim()) return;

            console.log("📩 Command:", text);

            const chatId = msg.key.remoteJid;

            // TODO:
            // Send text to FastAPI agent
            //
            const response = await askAgent(text);

            // const response =
            //     `Agent received: ${text}`;

            await sock.sendMessage(chatId, {
                text: response
            });

        } catch (error) {
            console.error(
                "Message processing error:",
                error
            );
        }
    });
}

connect().catch(console.error);