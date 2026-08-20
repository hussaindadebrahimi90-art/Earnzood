const http = require("http");

const PORT = process.env.PORT || 10000;

const server = http.createServer((req, res) => {
  res.writeHead(200, {
    "Content-Type": "application/json"
  });

  res.end(JSON.stringify({
    app: "EarnZood",
    status: "online"
  }));
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`EarnZood API running on port ${PORT}`);
});
