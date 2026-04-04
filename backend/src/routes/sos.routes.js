import express from "express";
import { triggerSOS, getSOSStatus } from "../controllers/sos.controllers.js";

const router = express.Router();

router.post("/trigger", triggerSOS);

// ✅ make it explicit
router.get("/status/:id", getSOSStatus);

export default router;