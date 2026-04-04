import axios from "axios";

export const sendSMS = async (to, message) => {
    try {
        const response = await axios.post(
            "https://www.fast2sms.com/dev/bulkV2",
            {
                route: "q",
                message: message,
                language: "english",
                numbers: String(to),
                sender_id: "FSTSMS"
            },
            {
                headers: {
                    authorization: process.env.FAST2SMS_API_KEY,
                    "Content-Type": "application/json"
                }
            }
        );

        console.log("📡 Response:", response.data);

        return response.data.return === true;

    } catch (error) {
        console.error("❌ Full Error:", error.response?.data || error.message);
        return false;
    }
};