import express from "express";
import redis from "../config/redis.js";
import User from "../models/user.js";

const router = express.Router();


// ===================== SIGNUP =====================
router.post("/signup", async (req, res) => {
    try {
        const { name, phone, email } = req.body;

        if (!name || !phone) {
            return res.status(400).json({
                error: "Name and phone required"
            });
        }

        // 🔹 Check in MongoDB
        const existingUser = await User.findOne({ phone });

        if (existingUser) {
            return res.status(400).json({
                error: "User already exists"
            });
        }

        // 🔹 Save to MongoDB
        const newUser = new User({
            name,
            phone,
            email
        });

        await newUser.save();
        console.log("✅ Saved to MongoDB:", newUser);

        // 🔹 Cache in Redis
        await redis.set(
            `user:${phone}`,
            JSON.stringify(newUser)
        );

        res.json({
            status: "signup successful",
            user: newUser
        });

    } catch (err) {
        console.error("Signup error:", err);
        res.status(500).json({
            error: "Server error"
        });
    }
});


// ===================== LOGIN =====================
router.post("/login", async (req, res) => {
    try {
        const { phone } = req.body;

        if (!phone) {
            return res.status(400).json({
                error: "Phone required"
            });
        }

        // 🔹 Try Redis first
        let user = await redis.get(`user:${phone}`);

        if (user) {
            return res.json({
                status: "login success (cache)",
                user: JSON.parse(user)
            });
        }

        // 🔹 Fallback to MongoDB
        user = await User.findOne({ phone });

        if (!user) {
            return res.status(404).json({
                error: "User not found"
            });
        }

        // 🔹 Cache again
        await redis.set(
            `user:${phone}`,
            JSON.stringify(user)
        );

        res.json({
            status: "login successful",
            user
        });

    } catch (err) {
        console.error("Login error:", err);
        res.status(500).json({
            error: "Server error"
        });
    }
});


// ===================== SAVE CONTACTS =====================
router.post("/contacts", async (req, res) => {
    try {
        const { phone, contacts } = req.body;

        if (!phone || !contacts || contacts.length === 0) {
            return res.status(400).json({
                error: "Phone and contacts required"
            });
        }

        // 🔹 Check user exists
        const user = await User.findOne({ phone });

        if (!user) {
            return res.status(404).json({
                error: "User not found"
            });
        }

        // 🔹 Save contacts in MongoDB
        user.contacts = contacts;
        await user.save();

        // 🔹 Cache contacts in Redis
        await redis.set(
            `contacts:${phone}`,
            JSON.stringify(contacts)
        );

        res.json({
            status: "contacts saved successfully",
            contacts
        });

    } catch (err) {
        console.error("Contacts error:", err);
        res.status(500).json({
            error: "Server error"
        });
    }
});


// ===================== GET CONTACTS =====================
router.get("/contacts/:phone", async (req, res) => {
    try {
        const { phone } = req.params;

        // 🔹 Try Redis first
        let contacts = await redis.get(`contacts:${phone}`);

        if (contacts) {
            return res.json({
                contacts: JSON.parse(contacts)
            });
        }

        // 🔹 Fallback to MongoDB
        const user = await User.findOne({ phone });

        if (!user || !user.contacts) {
            return res.json({
                contacts: []
            });
        }

        // 🔹 Cache again
        await redis.set(
            `contacts:${phone}`,
            JSON.stringify(user.contacts)
        );

        res.json({
            contacts: user.contacts
        });

    } catch (err) {
        console.error("Get contacts error:", err);
        res.status(500).json({
            error: "Server error"
        });
    }
});


export default router;