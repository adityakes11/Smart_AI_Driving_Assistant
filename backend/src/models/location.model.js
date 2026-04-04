import mongoose from "mongoose";

const locationSchema = new mongoose.Schema({
    phone: {
        type: String,
        required: true
    },
    lat: {
        type: Number,
        required: true
    },
    lng: {
        type: Number,
        required: true
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

export default mongoose.model("Location", locationSchema);