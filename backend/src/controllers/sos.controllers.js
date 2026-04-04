import mongoose from "mongoose";
import SOS from "../models/sos.model.js";
import Location from "../models/location.model.js";
import redis from "../config/redis.js";

export const triggerSOS = async (req, res) => {
    try {
        console.log("\n🚨 [SOS TRIGGER] HIT:", req.body);

        // ✅ FIXED: include userId
        const { phone, userId, severity, reasons } = req.body;

        // 🔒 Validation
        if (!phone) {
            return res.status(400).json({ error: "Phone is required" });
        }

        if (!userId) {
            return res.status(400).json({ error: "userId is required" });
        }

        console.log("DEBUG userId:", userId);

        // 🔥 Normalize phone
        const cleanPhone = phone.replace("+91", "");

        // 🔹 Try Redis first
        let locationData =
            (await redis.get(`location:${phone}`)) ||
            (await redis.get(`location:${cleanPhone}`));

        let lat, lng;

        if (locationData) {
            const parsed = JSON.parse(locationData);
            lat = parsed.lat;
            lng = parsed.lng;
            console.log("📍 Using Redis location:", lat, lng);
        } else {
            console.log("⚠️ Redis miss → checking MongoDB");

            const lastLocation = await Location.findOne({
                phone: { $in: [phone, cleanPhone] }
            }).sort({ createdAt: -1 });

            if (!lastLocation) {
                console.log("❌ No location found anywhere");
                return res.status(400).json({
                    error: "Location not available"
                });
            }

            lat = lastLocation.lat;
            lng = lastLocation.lng;

            console.log("📍 Using DB location:", lat, lng);
        }

        // 🔥 Convert numeric severity → enum
        let severityLevel = "LOW";

        if (typeof severity === "number") {
            if (severity >= 70) severityLevel = "SEVERE";
            else if (severity >= 40) severityLevel = "MEDIUM";
        } else if (typeof severity === "string") {
            severityLevel = severity;
        }

        console.log("⚡ Final severity:", severityLevel);

        // 🔹 Save SOS in DB
        const sosEvent = await SOS.create({
            phone,
            lat,
            lng,
            status: "triggered",
            severity: severityLevel,
            reasons: reasons || []
        });

        console.log("✅ SOS saved:", sosEvent._id);

        // 🔹 Push to Redis queue
        const queuePayload = {
            id: sosEvent._id.toString(),
            userId: userId,   // ✅ FIXED
            phone,
            lat,
            lng,
            status: "triggered",
            severity: severityLevel
        };

        await redis.lPush("sos_queue", JSON.stringify(queuePayload));

        console.log("📦 Pushed to queue:", queuePayload);

        // 🔹 Response
        res.json({
            success: true,
            message: "SOS triggered successfully",
            id: sosEvent._id,
            location: { lat, lng },
            severity: severityLevel
        });

    } catch (err) {
        console.error("❌ SOS error:", err);
        res.status(500).json({ error: "Server error" });
    }
};

export const getSOSStatus = async (req, res) => {
    try {
        const { id } = req.params;

        console.log("\n📊 [SOS STATUS] Request for:", id);

        // 🔥 Prevent invalid ObjectId crash
        if (!mongoose.Types.ObjectId.isValid(id)) {
            return res.status(400).json({
                error: "Invalid SOS ID"
            });
        }

        const sos = await SOS.findById(id);

        if (!sos) {
            return res.status(404).json({ error: "Not found" });
        }

        res.json({
            success: true,
            status: sos.status,
            phone: sos.phone,
            severity: sos.severity,
            reasons: sos.reasons,
            location: {
                lat: sos.lat,
                lng: sos.lng
            }
        });

    } catch (err) {
        console.error("❌ Status error:", err);
        res.status(500).json({ error: "Server error" });
    }
};