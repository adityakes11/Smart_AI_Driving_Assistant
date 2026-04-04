import { Server } from "socket.io";

let io;

export const initSocket = (server) => {
  io = new Server(server, {
    cors: { origin: "*" }
  });

  io.on("connection", (socket) => {
    console.log("User connected:", socket.id);

    socket.on("register", (userId) => {
      socket.join(userId);
      console.log(`User ${userId} joined room`);
    });
  });

  return io;
};

export const getIO = () => io;