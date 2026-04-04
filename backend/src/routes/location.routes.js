import express from "express";
import { updateLocation } from "../controllers/location.controller.js";

console.log("📍 LOCATION ROUTES LOADED");

const router = express.Router();

router.post("/update", updateLocation);

export default router;