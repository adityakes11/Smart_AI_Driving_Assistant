import dotenv from "dotenv";
dotenv.config();

import { sendSMS } from "./src/service/notification.service.js";

async function test() {
    console.log("🚀 Testing SMS...");

    const success = await sendSMS(
        "8004663564", // 👈 without +91
        "Accident Alert! Location: https://maps.google.com/?q=28.6139,77.209"

    );
    console.error("❌ Full Error:", error.response?.data || error.message);

    console.log("Result:", success);
}

test();