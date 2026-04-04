import express from "express";
import cors from "cors";

import userRoutes from "./routes/user.routes.js";
import sosRoutes from "./routes/sos.routes.js";

const app = express();

app.use(cors());
app.use(express.json());

app.use("/api/user", userRoutes);
app.use("/api/sos", sosRoutes);

export default app;