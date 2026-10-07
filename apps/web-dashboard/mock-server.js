const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const crypto = require("crypto");

const app = express();
app.use(express.json({ limit: "5mb" }));
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "Content-Type, Authorization");
  res.header("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
  if (req.method === "OPTIONS") return res.sendStatus(200);
  next();
});

let tables = [
  { id: "1", restaurant_id: "r1", number_label: "T1", capacity: 2, zone: "Interieur", status: "FREE" },
  { id: "2", restaurant_id: "r1", number_label: "T2", capacity: 4, zone: "Terrasse", status: "RESERVED" },
  { id: "3", restaurant_id: "r1", number_label: "T3", capacity: 6, zone: "VIP", status: "OCCUPIED" },
  { id: "4", restaurant_id: "r1", number_label: "T4", capacity: 2, zone: "Interieur", status: "LOCKED" },
];

let reservations = [
  {
    id: "res1", restaurant_id: "r1", table_id: "2",
    customer_name: "Jean Kabila", customer_phone: "+243900000000",
    reservation_date: new Date(Date.now() + 3600 * 1000).toISOString(),
    guests_count: 4, status: "CONFIRMED", deposit_amount: 10,
    qr_code_token: "abc123", created_at: new Date().toISOString(),
  },
];

app.get("/tables", (req, res) => res.json(tables));
require("./mock-restaurants")(app);
app.get("/reservations", (req, res) => res.json(reservations));
app.patch("/settings/agent", (req, res) => res.json({ enabled: req.body.enabled }));
app.post("/auth/login", (req, res) => res.json({ access_token: "fake-jwt-dev" }));

app.get("/analytics/attendance", (req, res) => res.json([
  { day: "Lun", guests: 24 }, { day: "Mar", guests: 32 }, { day: "Mer", guests: 18 },
  { day: "Jeu", guests: 40 }, { day: "Ven", guests: 55 }, { day: "Sam", guests: 70 }, { day: "Dim", guests: 60 },
]));

app.get("/analytics/popular-dishes", (req, res) => res.json([
  { name: "Poulet Moambe", value: 40 }, { name: "Poisson Braise", value: 25 },
  { name: "Riz Sauce Graine", value: 20 }, { name: "Brochettes", value: 15 },
]));

app.get("/analytics/revenue-forecast", (req, res) => res.json([
  { month: "Jan", revenue: 1200 }, { month: "Fev", revenue: 1450 },
  { month: "Mar", revenue: 1700 }, { month: "Avr", revenue: 1600 },
]));

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

io.on("connection", (socket) => {
  socket.on("client_message", (msg) => {
    socket.emit("agent_typing");
    setTimeout(() => {
      socket.emit("agent_message", {
        id: crypto.randomUUID(), role: "agent",
        text: `Reponse simulee a: "${msg.text}"`,
        timestamp: new Date().toISOString(),
      });
    }, 1000);
  });
});

// Simule un changement de statut de table toutes les 15 secondes
setInterval(() => {
  const table = tables[Math.floor(Math.random() * tables.length)];
  const statuses = ["FREE", "RESERVED", "OCCUPIED", "LOCKED"];
  table.status = statuses[Math.floor(Math.random() * statuses.length)];
  io.emit("table_status_update", table);
}, 15000);

server.listen(8000, () => console.log("Mock API + WebSocket sur http://localhost:8000"));