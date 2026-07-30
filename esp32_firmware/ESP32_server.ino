#include <WiFi.h>

const char* ssid = "YOUR_WIFI_SSID"; // 2.4GHz only
const char* password = "YOUR_WIFI_PASSWORD";

WiFiServer server(80);

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();

  if (client) {
    String request = "";
    while (client.connected() && client.available()) {
      char c = client.read();
      request += c;
      if (c == '\n') break; 
    }

    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/html");
    client.println("Connection: close");
    client.println();

    client.println(R"HTML(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ESP32 Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background: linear-gradient(135deg, #1e3c72, #2a5298);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .card {
      background: #ffffff;
      border-radius: 16px;
      padding: 32px 28px;
      max-width: 380px;
      width: 100%;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      text-align: center;
    }
    .icon {
      font-size: 48px;
      margin-bottom: 10px;
    }
    h1 {
      color: #1e3c72;
      font-size: 22px;
      margin-bottom: 6px;
    }
    p.subtitle {
      color: #888;
      font-size: 13px;
      margin-bottom: 24px;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #e8f8ee;
      color: #1a7f4b;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 20px;
    }
    .dot {
      width: 8px;
      height: 8px;
      background: #22c55e;
      border-radius: 50%;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.3; }
      100% { opacity: 1; }
    }
    .info-row {
      display: flex;
      justify-content: space-between;
      padding: 10px 0;
      border-bottom: 1px solid #f0f0f0;
      font-size: 14px;
    }
    .info-row:last-child { border-bottom: none; }
    .label { color: #888; }
    .value { color: #1e3c72; font-weight: 600; }
    .footer {
      margin-top: 20px;
      font-size: 11px;
      color: #bbb;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">📡</div>
    <h1>ESP32 Dashboard</h1>
    <p class="subtitle">Live device status</p>

    <div class="status">
      <span class="dot"></span> Online
    </div>

    <div class="info-row">
      <span class="label">Chip</span>
      <span class="value">ESP32-D0WD-V3</span>
    </div>
    <div class="info-row">
      <span class="label">Wi-Fi</span>
      <span class="value">Connected</span>
    </div>
    <div class="info-row">
      <span class="label">Server</span>
      <span class="value">Running</span>
    </div>

    <div class="footer">Refresh the page to check live status</div>
  </div>
</body>
</html>
    )HTML");

    client.stop();
  }
}