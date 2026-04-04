import redisClient from "../config/redis.js";

export const setupUser = async (req, res) => {
  try {
    const { name, contacts, phone } = req.body;

    // 🔒 Validation
    if (!phone || !contacts || contacts.length === 0) {
      return res.status(400).json({
        error: "Phone and contacts are required"
      });
    }

    const userId = phone; // 🔥 KEY CHANGE

    const userData = {
      name,
      phone,
      contacts
    };

    // 🔥 Save using phone as key
    await redisClient.set(`user:${userId}`, JSON.stringify(userData));

    res.json({
      userId,
      message: "User registered successfully"
    });

  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};