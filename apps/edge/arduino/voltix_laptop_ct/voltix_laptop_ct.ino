#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <DHT.h>
#include <WiFiS3.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#define DHTPIN 5
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Nothing Phone";
const char* password = "12345678";

// 60-Second Demo Cycle for SIH Video:
// 00s - 10s: IDLE   (Charger in socket, unplugged from laptop)  -> ~0.05 A, ~11.5 W
// 10s - 35s: ACTIVE (Plugged into laptop, 135W active load)     -> ~0.58 A, ~132.8 W
// 35s - 45s: IDLE   (Unplugged from laptop, socket still ON)    -> ~0.05 A, ~11.2 W
// 45s - 60s: OFF    (Wall socket switched OFF)                  ->  0.00 A,   0.0 W
const unsigned long CYCLE_SECONDS = 60;
unsigned long demoStartTime = 0;
unsigned long lastDisplayUpdate = 0;
const unsigned long DISPLAY_INTERVAL = 1000; // update OLED every 1 second

void showStatus(const char* line1, const char* line2 = "", const char* line3 = "") {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(0, 0);
  display.println(line1);
  display.setCursor(0, 20);
  display.println(line2);
  display.setCursor(0, 40);
  display.println(line3);
  display.display();
}

void showLiveDemo(const char* state, int elapsedSec, float current, float voltage, float power, float temperature) {
  display.clearDisplay();
  display.setTextColor(SH110X_WHITE);

  // Line 1: Header + Elapsed Second Counter (helps you time physical actions on camera!)
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("LAPTOP 135W  ");
  if (elapsedSec < 10) display.print("0");
  display.print(elapsedSec);
  display.print("s");

  display.drawLine(0, 10, 127, 10, SH110X_WHITE);

  // Line 2: Big State display
  display.setCursor(0, 14);
  display.print("STATE: ");
  display.print(state);

  // Line 3: Current
  display.setCursor(0, 26);
  display.print("Current : ");
  display.print(current, 2);
  display.print(" A");

  // Line 4: Voltage
  display.setCursor(0, 38);
  display.print("Voltage : ");
  display.print(voltage, 1);
  display.print(" V");

  // Line 5: Power
  display.setCursor(0, 50);
  display.print("Power   : ");
  display.print(power, 1);
  display.print(" W");

  display.display();
}

void setup_wifi() {
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  showStatus("WiFi Connecting...", ssid);

  WiFi.disconnect();
  delay(1000);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;

    if (attempts >= 15) {
      Serial.println();
      Serial.println("WiFi timeout — proceeding in standalone demo mode");
      showStatus("WiFi Skipped", "Demo Mode Ready");
      delay(1500);
      return;
    }
  }

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("Arduino IP: ");
  Serial.println(WiFi.localIP());

  String ip = WiFi.localIP().toString();
  showStatus("WiFi Connected", ip.c_str());
  delay(1500);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("=========================================");
  Serial.println("  ARDUINO UNO R4 - VOLTIX 135W DEMO");
  Serial.println("=========================================");

  Wire.begin();

  if (!display.begin(0x3C, true)) {
    Serial.println("OLED initialization failed!");
    while (1) {
      delay(1000);
    }
  }

  display.clearDisplay();
  display.display();

  showStatus("VOLTIX MONITOR", "135W Laptop Demo", "Starting...");
  delay(1500);

  dht.begin();
  delay(1000);

  randomSeed(analogRead(A0));

  setup_wifi();

  demoStartTime = millis();
}

void loop() {
  unsigned long now = millis();

  if (now - lastDisplayUpdate >= DISPLAY_INTERVAL) {
    lastDisplayUpdate = now;

    unsigned long totalElapsedSec = (now - demoStartTime) / 1000;
    int currentSec = totalElapsedSec % CYCLE_SECONDS;

    float temperature = dht.readTemperature();
    if (isnan(temperature)) {
      temperature = 31.0 + (random(0, 30) / 10.0);
    }

    const char* state = "IDLE";
    float current = 0.0;
    float voltage = 0.0;
    float power = 0.0;

    // Phase 1: 0s to 10s -> IDLE (Charger in socket, cable unplugged from laptop)
    if (currentSec < 10) {
      state = "IDLE";
      current = 0.045 + (random(0, 15) / 1000.0);       // ~0.045A - 0.055A
      voltage = 229.5 + (random(0, 20) / 10.0);        // ~229.5V - 231.5V
      power   = voltage * current * 0.95;              // ~10.5W - 12.0W
    }
    // Phase 2: 10s to 35s -> ACTIVE (Plugged into laptop, 135W active charging/running load)
    else if (currentSec < 35) {
      state = "ACTIVE";
      current = 0.560 + (random(0, 50) / 1000.0);       // ~0.560A - 0.610A
      voltage = 228.0 + (random(0, 25) / 10.0);        // ~228.0V - 230.5V
      power   = voltage * current * 0.96;              // ~125.0W - 138.0W
    }
    // Phase 3: 35s to 45s -> IDLE (Cable unplugged from laptop, wall socket still ON)
    else if (currentSec < 45) {
      state = "IDLE";
      current = 0.045 + (random(0, 15) / 1000.0);       // ~0.045A - 0.055A
      voltage = 229.5 + (random(0, 20) / 10.0);        // ~229.5V - 231.5V
      power   = voltage * current * 0.95;              // ~10.5W - 12.0W
    }
    // Phase 4: 45s to 60s -> OFF (Wall socket switched OFF)
    else {
      state = "OFF";
      current = 0.00;
      voltage = 0.0;
      power   = 0.0;
    }

    // Print to Serial for debugging & logging
    Serial.print("[");
    if (currentSec < 10) Serial.print("0");
    Serial.print(currentSec);
    Serial.print("s] State: ");
    Serial.print(state);
    Serial.print(" | I = ");
    Serial.print(current, 3);
    Serial.print(" A | V = ");
    Serial.print(voltage, 1);
    Serial.print(" V | P = ");
    Serial.print(power, 1);
    Serial.print(" W | Temp = ");
    Serial.print(temperature, 1);
    Serial.println(" C");

    showLiveDemo(state, currentSec, current, voltage, power, temperature);
  }
}
