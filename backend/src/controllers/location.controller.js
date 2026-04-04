import redis from "../config/redis.js";
import Location from "../models/location.model.js"; 

export const updateLocation = async (req, res) => {
    try {
        console.log("\n📍 [LOCATION UPDATE] HIT:", req.body);

        const { phone, lat, lng } = req.body;

        if (!phone || !lat || !lng) {
            console.log("❌ Missing fields");
            return res.status(400).json({ error: "Missing data" });
        }

        const locationData = { lat, lng };

        // 🔥 Save latest location in Redis
        await redis.set(`location:${phone}`, JSON.stringify(locationData));

        // 🔥 Save location history in MongoDB
        await Location.create({
            phone,
            lat,
            lng
        });

        console.log("✅ Location stored in Redis + MongoDB");

        res.json({
            success: true,
            message: "Location saved successfully"
        });

    } catch (err) {
        console.error("❌ Location error:", err);
        res.status(500).json({ error: "Server error" });
    }
};