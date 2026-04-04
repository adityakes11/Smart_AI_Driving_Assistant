import mongoose from "mongoose";

const sosSchema = new mongoose.Schema({
    phone: String,
    lat: Number,
    lng: Number,

    status: {
        type: String,
        enum: ["triggered", "processing", "sent", "failed"],
        default: "triggered"
    },

    severity: {
        type: String,
        enum: ["LOW", "MEDIUM", "SEVERE"],
        default: "LOW"
    },

    reasons: [String]
});

const SOS = mongoose.model("SOS", sosSchema);

export default SOS; // ✅ THIS IS THE FIX