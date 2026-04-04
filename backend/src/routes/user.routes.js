import express from "express";
import { setupUser } from "../controllers/user.controllers.js";
const router = express.Router();

router.post("/setup", setupUser);

export default router;