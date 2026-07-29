/*
 * J.A.R.V.I.S Remote PC Controller - ESP32 Firmware
 * --------------------------------------------------
 * Functions:
 * 1. WiFi & Tailscale/Local Network Connectivity
 * 2. Wake-on-LAN (WoL) Magic Packet Sender to wake target PC
 * 3. Hardware Relay trigger option (Optocoupler / Power Switch header)
 * 4. PC Heartbeat / Ping monitor (Checks if PC is ON or OFF)
 * 5. REST API server for control (/wake, /status, /relay)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <WebServer.h>
#include <ESPmDNS.h>

// ================= CONFIGURATION =================
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// Target PC Network Configuration
const char* TARGET_PC_IP = "192.168.1.100";           // Local IP of your PC
uint8_t TARGET_MAC[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF}; // Replace with your PC MAC Address

// Hardware Pin Setup
const int RELAY_PIN = 18;       // GPIO connected to Relay / Optocoupler for Power Button
const int STATUS_LED = 2;       // Onboard LED
const int SENSE_PIN = 34;       // Optional 5V USB sensing from PC to check power state

// Port & Server Configuration
WebServer server(80);
WiFiUDP udp;
const uint16_t WOL_PORT = 9;

// ================= FUNCTIONS =================

// Send Wake-on-LAN Magic Packet
bool sendWOL(const uint8_t* mac) {
  uint8_t magicPacket[102];
  
  // First 6 bytes are 0xFF
  for (int i = 0; i < 6; i++) {
    magicPacket[i] = 0xFF;
  }
  
  // Repeat MAC address 16 times
  for (int i = 0; i < 16; i++) {
    for (int j = 0; j < 6; j++) {
      magicPacket[6 + (i * 6) + j] = mac[j];
    }
  }
  
  // Broadcast to UDP port 9
  IPAddress broadcastIP(255, 255, 255, 255);
  udp.beginPacket(broadcastIP, WOL_PORT);
  udp.write(magicPacket, sizeof(magicPacket));
  bool success = udp.endPacket();
  
  Serial.println(success ? "[WOL] Magic packet sent successfully!" : "[WOL] Failed to send packet!");
  return success;
}

// REST Handlers
void handleRoot() {
  String json = "{";
  json += "\"device\":\"JARVIS_ESP32_Node\",";
  json += "\"status\":\"online\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"uptime_sec\":" + String(millis() / 1000);
  json += "}";
  server.send(200, "application/json", json);
}

void handleWake() {
  digitalWrite(STATUS_LED, HIGH);
  bool sent = sendWOL(TARGET_MAC);
  digitalWrite(STATUS_LED, LOW);
  
  String response = "{";
  response += "\"action\":\"wake\",";
  response += "\"success\":" + String(sent ? "true" : "false") + ",";
  response += "\"target_mac\":\"";
  for(int i=0; i<6; i++) {
    char buf[3];
    sprintf(buf, "%02X", TARGET_MAC[i]);
    response += buf;
    if(i < 5) response += ":";
  }
  response += "\"}";
  
  server.send(200, "application/json", response);
}

void handleRelay() {
  digitalWrite(STATUS_LED, HIGH);
  // Pulse power pin for 500ms to simulate physical button press
  digitalWrite(RELAY_PIN, HIGH);
  delay(500);
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(STATUS_LED, LOW);

  server.send(200, "application/json", "{\"action\":\"relay_pulse\",\"success\":true}");
}

void handleStatus() {
  bool pcOn = false;
  // If USB sense pin is high or analog reading > 2000, PC power USB is delivering 5V
  int senseVal = analogRead(SENSE_PIN);
  if (senseVal > 1500) {
    pcOn = true;
  }

  String json = "{";
  json += "\"pc_status\":\"" + String(pcOn ? "ON" : "OFF_OR_STANDBY") + "\",";
  json += "\"sense_value\":" + String(senseVal);
  json += "}";
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  pinMode(STATUS_LED, OUTPUT);
  digitalWrite(STATUS_LED, LOW);

  pinMode(SENSE_PIN, INPUT);

  Serial.println("\n[JARVIS ESP32 Node] Starting...");
  
  // WiFi Connection
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  Serial.print("Connecting to WiFi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());

    // Setup mDNS
    if (MDNS.begin("jarvis-esp32")) {
      Serial.println("[mDNS] Responder started at http://jarvis-esp32.local");
    }

    // Register REST endpoints
    server.on("/", HTTP_GET, handleRoot);
    server.on("/wake", HTTP_GET, handleWake);
    server.on("/relay", HTTP_POST, handleRelay);
    server.on("/status", HTTP_GET, handleStatus);

    server.begin();
    Serial.println("[HTTP Server] Listening on port 80");
  } else {
    Serial.println("\n[WiFi] Failed to connect! Retrying in background...");
  }
}

void loop() {
  // Maintain WiFi Connection
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long lastReconnect = 0;
    if (millis() - lastReconnect > 10000) {
      lastReconnect = millis();
      WiFi.reconnect();
    }
  } else {
    server.handleClient();
  }
}
