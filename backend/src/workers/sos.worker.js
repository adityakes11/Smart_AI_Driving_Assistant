import connectDB from "../config/db.js";
import redis from "../config/redis.js";
import SOS from "../models/sos.model.js";

// 🚀 Initialize Worker
async function init() {
    try {
        console.log("🚀 SOS Worker starting...");

        await connectDB();
        console.log("✅ MongoDB connected in worker");

        startWorker();

    } catch (err) {
        console.error("❌ Worker init failed:", err);
        process.exit(1);
    }
}

// 🔁 Worker Loop
async function startWorker() {
    console.log("🚀 SOS Worker started...");

    while (true) {
        try {
            const data = await redis.brPop("sos_queue", 0);
            if (!data) continue;

            const event = JSON.parse(data.element);

            console.log("\n🚨 [WORKER] Received SOS:", event);

            await handleSOS(event);

        } catch (error) {
            console.error("❌ Worker loop error:", error);
        }
    }
}

// 🧠 SOS Handler
async function handleSOS(event) {
    const { id, userId, phone, lat, lng, severity } = event;

    try {
        console.log("🔄 Processing SOS ID:", id);

        if (!userId) {
            console.log("❌ Missing userId in event");
            return;
        }

        await SOS.findByIdAndUpdate(id, {
            status: "processing",
            updatedAt: new Date()
        });

        // 🔥 Fetch user
        const userData = await redis.get(`user:${userId}`);

        if (!userData) {
            console.log("❌ User not found in Redis:", userId);
            return;
        }

        const user = JSON.parse(userData);
        const contacts = user.contacts || [];

        console.log("📞 Contacts:", contacts.length);

        if (contacts.length === 0) {
            console.log("❌ No contacts available");
            return;
        }

        const message = buildMessage(phone, lat, lng, severity);

        let allSuccess = true;

        // 🔥 SIMULATED SMS FUNCTION
        const simulateSMS = async (phone, message) => {
            const time = new Date().toLocaleString();

            console.log(`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📩 EMERGENCY ALERT DISPATCHED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 To   : ${phone}
🕒 Time : ${time}
📍 Message:
${message}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            `);

            // simulate delay
            await new Promise((res) => setTimeout(res, 300));

            return true;
        };

        // 🔥 Send to contacts
        for (let c of contacts) {
            const cleanNumber = c.phone.replace("+91", "");

            console.log("📩 Sending SMS to:", cleanNumber);

            const success = await simulateSMS(cleanNumber, message);

            if (!success) {
                console.log("❌ SMS failed:", cleanNumber);
                allSuccess = false;
            }
        }

        if (allSuccess) {
            console.log("✅ All alerts sent");

            await SOS.findByIdAndUpdate(id, {
                status: "sent",
                resolvedAt: new Date()
            });

        } else {
            console.log("❌ Some alerts failed → retry");

            await SOS.findByIdAndUpdate(id, {
                status: "failed"
            });

            await redis.lPush("retry_queue", JSON.stringify(event));
        }

    } catch (err) {
        console.error("❌ Error handling SOS:", err);
        await redis.lPush("retry_queue", JSON.stringify(event));
    }
}

// 📨 Message Builder
function buildMessage(phone, lat, lng, severity) {
    return `
🚨 ACCIDENT ALERT 🚨

User: ${phone}
Severity: ${severity}

📍 Coordinates:
Latitude : ${lat}
Longitude: ${lng}

🗺️ Map:
https://maps.google.com/?q=${lat},${lng}

Immediate help required.
`;
}

// 🚀 Start
init();