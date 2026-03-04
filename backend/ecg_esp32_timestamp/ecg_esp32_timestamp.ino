#include <WiFi.h>

const char* ssid     = "yourid";
const char* password = "yourpwd";

WiFiServer server(80);

// ECG Pins
const int LO_PLUS    = 14;
const int LO_MINUS   = 27;
const int ECG_ANALOG = 34;

// Button Pins and Debounce Variables
const int buttonPin = 12;     // Connect button between this pin and GND
int isExercise = 0;           // 0 = REST, 1 = EXERCISE
int buttonState;
int lastButtonState = HIGH;   // INPUT_PULLUP
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Sampling Timing
unsigned long t_prev = 0;
const unsigned long Ts = 6250; // 160Hz (in microseconds)

void setup() {
  Serial.begin(115200);

  pinMode(LO_PLUS, INPUT);
  pinMode(LO_MINUS, INPUT);
  pinMode(ECG_ANALOG, INPUT);

  pinMode(buttonPin, INPUT_PULLUP);

  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
}

void loop() {
  WiFiClient client = server.available();

  if (client) {
    Serial.println("Client Connected");
    while (client.connected()) {

      // --- 1) button ---
      int reading = digitalRead(buttonPin);

      if (reading != lastButtonState) {
        lastDebounceTime = millis();
      }

      if ((millis() - lastDebounceTime) > debounceDelay) {
        if (reading != buttonState) {
          buttonState = reading;
          if (buttonState == LOW) {
            isExercise = !isExercise;
            Serial.print("Mode Toggled to: ");
            Serial.println(isExercise ? "EXERCISE" : "REST");
          }
        }
      }
      lastButtonState = reading;

      // --- 2) ECG ---
      unsigned long t_now = micros();
      if (t_now - t_prev >= Ts) {
        t_prev = t_now;

        int lo_p = digitalRead(LO_PLUS);
        int lo_m = digitalRead(LO_MINUS);

        // lead-off detection
        int leadOff = (lo_p == HIGH || lo_m == HIGH) ? 1 : 0;

        // Sender-side timestamp (use the sampling instant)
        unsigned long t_sample_us = t_now;

        String dataPacket;

        if (leadOff) {
          // format: time_us,isExercise,NaN
          dataPacket = String(t_sample_us) + "," + String(isExercise) + ",NaN";
        } else {
          int x = analogRead(ECG_ANALOG);
          float voltage = (x / 4095.0f) * 3.3f;
          // format: time_us,isExercise,voltage
          dataPacket = String(t_sample_us) + "," + String(isExercise) + "," + String(voltage, 2);
        }

        client.println(dataPacket);
      }
    }
    Serial.println("Client Disconnected");
  }
}