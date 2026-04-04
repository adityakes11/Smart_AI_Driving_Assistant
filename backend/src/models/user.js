import mongoose from "mongoose";

const userSchema = new mongoose.Schema({
    name: String,
    phone: { type: String, unique: true },
    email: String,
    contacts: [
        {
            name: String,
            phone: String
        }
    ]
});

export default mongoose.model("User", userSchema);