/*
 * JAWIR OS - Fire Detector ESP32 Firmware
 * =========================================
 * Fixed version with correct MQTT credentials and device_id
 * 
 * Hardware:
 *   - ESP32 DevKit
 *   - DHT11 (pin 23)
 *   - MQ-2 Gas sensor (A: pin 34, D: pin 27)
 *   - Flame sensor (pin 26)
 *   - Buzzer (pin 25)
 *   - I2C LCD 16x2 (SDA: 21, SCL: 22)
 * 
 * MQTT Topics (for JAWIR integration):
 *   - Telemetry: nimak/deteksi-api/telemetry
 *   - Command:   nimak/deteksi-api/cmd
 *   - Event:     lab/zaks/event
 *   - Status:    lab/zaks/status
 *   - Alert:     lab/zaks/alert
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <time.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "DHT.h"

// ===== Hardware Pins =====
#define SDA_PIN        21
#define SCL_PIN        22
#define DHTPIN         23
#define DHTTYPE        DHT11        
#define GAS_ANALOG     34           
#define GAS_DIGITAL    27           
#define FLAME_PIN      26           
#define BUZZER_PIN     25

// =====================================================
//  ⚠️ EDIT BAGIAN INI SESUAI JARINGAN ANDA
// =====================================================
const char* WIFI_SSID = "RedmiNote13";       // <-- Ganti dengan nama WiFi Anda
const char* WIFI_PASS = "naufal.453";        // <-- Ganti dengan password WiFi Anda

// ===== MQTT (HiveMQ Cloud TLS) - JANGAN DIUBAH =====
const char* MQTT_HOST = "6975c5257bf14a6380bdd8d8cd5613ee.s1.eu.hivemq.cloud";
const uint16_t MQTT_PORT = 8883;
const char* MQTT_USER = "Jawir";
const char* MQTT_PASS = "@@U93BqZzU9mt6Q";   // <-- Password yang benar!

// ===== MQTT Topics (sesuai dengan backend JAWIR) =====
const char* TOPIC_PUB   = "nimak/deteksi-api/telemetry";
const char* TOPIC_SUB   = "nimak/deteksi-api/cmd";
const char* TOPIC_EVENT = "lab/zaks/event";
const char* TOPIC_LOG   = "lab/zaks/log";
const char* TOPIC_LWT   = "lab/zaks/status";
const char* TOPIC_ALERT = "lab/zaks/alert";

// ===== LCD & DHT =====
LiquidCrystal_I2C lcd(0x27, 16, 2);
DHT dht(DHTPIN, DHTTYPE);

// ===== MQTT client =====
WiFiClientSecure net;
PubSubClient mqtt(net);

// ===== State =====
int  GAS_THRESHOLD = 4095;
bool forceAlarm    = false;
bool prevFlame     = false;

unsigned long lastPub  = 0;
const unsigned long PUB_MS = 30000;   // Publish tiap 30 detik
unsigned long lastLcd  = 0;

float lastT = NAN, lastH = NAN;
unsigned long lastDht = 0;
const unsigned long DHT_PERIOD_MS = 1000;

// Timer untuk auto-off buzzer dari YOLO alert
unsigned long yoloAlarmTime = 0;
const unsigned long YOLO_ALARM_DURATION = 5000;

// ===== TLS Root CA (Let's Encrypt ISRG Root X1) =====
static const char* HIVEMQ_ROOT_CA = R"EOF(
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----
)EOF";

// ===== Utilities =====
String chipIdString() {
  uint64_t id = ESP.getEfuseMac();
  char buf[17];
  snprintf(buf, sizeof(buf), "%04X%08X", (uint16_t)(id>>32), (uint32_t)id);
  return String(buf);
}

void lcdPrint2(const char* l1, const char* l2) {
  char top[17], bot[17];
  snprintf(top, sizeof(top), "%-16s", l1);
  snprintf(bot, sizeof(bot), "%-16s", l2);
  lcd.setCursor(0,0); lcd.print(top);
  lcd.setCursor(0,1); lcd.print(bot);
}

void onMqttMsg(char* topic, byte* payload, unsigned int len) {
  String msg; msg.reserve(len);
  for (unsigned int i=0; i<len; i++) msg += (char)payload[i];
  Serial.printf("[MQTT] %s => %s\n", topic, msg.c_str());

  // Handle YOLO alert from camera
  if (strcmp(topic, TOPIC_ALERT) == 0) {
    Serial.println("[YOLO ALERT] Fire detected by camera!");
    forceAlarm = true;
    yoloAlarmTime = millis();
    
    char conf[80];
    snprintf(conf, sizeof(conf), "{\"event\":\"yolo_alarm_received\",\"id\":\"%s\"}", 
             chipIdString().c_str());
    mqtt.publish(TOPIC_EVENT, conf, false);
    return;
  }

  // Handle commands
  if (msg.equalsIgnoreCase("BUZZER_ON")) {
    forceAlarm = true;
    yoloAlarmTime = 0;
  }
  else if (msg.equalsIgnoreCase("BUZZER_OFF")) {
    forceAlarm = false;
    yoloAlarmTime = 0;
  }
  else if (msg.startsWith("THR=")) {
    GAS_THRESHOLD = msg.substring(4).toInt();
    Serial.printf("[MQTT] THR -> %d\n", GAS_THRESHOLD);
    char ebuf[64];
    snprintf(ebuf, sizeof(ebuf), "{\"event\":\"thr_update\",\"thr\":%d}", GAS_THRESHOLD);
    mqtt.publish(TOPIC_EVENT, ebuf, false);
  }
}

// ===== NTP time sync =====
void syncTime() {
  configTime(7 * 3600, 0, "pool.ntp.org", "time.nist.gov");

  time_t now = time(nullptr);
  while (now < 1700000000) {
    delay(300);
    now = time(nullptr);
  }
  struct tm timeinfo;
  gmtime_r(&now, &timeinfo);
  Serial.printf("Time synced: %04d-%02d-%02d %02d:%02d:%02d\n",
                timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
}

void wifiConnect() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("WiFi connect to %s ...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { 
    delay(250); 
    Serial.print("."); 
  }
  Serial.printf("\nWiFi OK, IP: %s\n", WiFi.localIP().toString().c_str());
  syncTime();
}

void mqttConnect() {
  net.setCACert(HIVEMQ_ROOT_CA);
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMsg);
  mqtt.setKeepAlive(30);
  mqtt.setBufferSize(512);

  while (!mqtt.connected()) {
    String cid = "esp32-fire-" + chipIdString();
    Serial.printf("MQTT connect %s ...\n", cid.c_str());
    const char* willMsg = "{\"status\":\"offline\"}";
    
    if (mqtt.connect(cid.c_str(), MQTT_USER, MQTT_PASS, TOPIC_LWT, 1, true, willMsg)) {
      Serial.println("MQTT OK");
      
      mqtt.subscribe(TOPIC_SUB);
      mqtt.subscribe(TOPIC_ALERT);
      
      mqtt.publish(TOPIC_LWT, "{\"status\":\"online\"}", true);
      mqtt.publish(TOPIC_EVENT, "{\"event\":\"boot\",\"status\":\"online\"}", false);
      
      Serial.println("Subscribed to:");
      Serial.printf("  - %s (commands)\n", TOPIC_SUB);
      Serial.printf("  - %s (YOLO alerts)\n", TOPIC_ALERT);
    } else {
      Serial.printf("MQTT rc=%d, retry...\n", mqtt.state());
      delay(1000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== JAWIR OS Fire Detector ===");

  // LCD I2C
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  lcd.init();
  lcd.backlight();
  lcdPrint2("JAWIR Fire Det", "WiFi init...");

  // Sensor
  dht.begin();
  pinMode(GAS_DIGITAL, INPUT_PULLUP);
  pinMode(FLAME_PIN,   INPUT_PULLUP);
  pinMode(BUZZER_PIN,  OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  analogReadResolution(12);
  analogSetPinAttenuation(GAS_ANALOG, ADC_11db);

  // Net
  wifiConnect();
  mqttConnect();

  lcd.clear();
  lcdPrint2("MQTT Connected!", WiFi.localIP().toString().c_str());
  delay(800);
  
  Serial.println("Setup complete!");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) wifiConnect();
  if (!mqtt.connected()) mqttConnect();
  mqtt.loop();

  // Auto-off YOLO alarm setelah 5 detik
  if (forceAlarm && yoloAlarmTime > 0) {
    if (millis() - yoloAlarmTime >= YOLO_ALARM_DURATION) {
      forceAlarm = false;
      yoloAlarmTime = 0;
      Serial.println("[YOLO ALARM] Auto-off");
      mqtt.publish(TOPIC_EVENT, "{\"event\":\"yolo_alarm_auto_off\"}", false);
    }
  }

  // DHT (rate-limit + cache)
  if (millis() - lastDht >= DHT_PERIOD_MS) {
    lastDht = millis();
    float _h = dht.readHumidity();
    float _t = dht.readTemperature();
    if (!isnan(_h) && !isnan(_t)) { 
      lastH = _h; 
      lastT = _t; 
    }
  }
  float h = lastH;
  float t = lastT;

  // GAS & FLAME
  int   gasAnalog = analogRead(GAS_ANALOG);
  uint32_t gasMv  = analogReadMilliVolts(GAS_ANALOG);
  bool  gasTrig   = (digitalRead(GAS_DIGITAL) == LOW);
  bool  flameTrig = (digitalRead(FLAME_PIN)   == LOW);

  // LOGIKA ALARM
  bool localFire = flameTrig || (gasAnalog >= GAS_THRESHOLD);
  bool fire = localFire || forceAlarm;
  digitalWrite(BUZZER_PIN, fire ? HIGH : LOW);

  // ALERT sekali saat flame detected
  if (flameTrig && !prevFlame) {
    char abuf[220];
    char tbuf[8], hbuf[8];
    if (isnan(t)) snprintf(tbuf, sizeof(tbuf), "null"); 
    else dtostrf(t, 4, 1, tbuf);
    if (isnan(h)) snprintf(hbuf, sizeof(hbuf), "null"); 
    else dtostrf(h, 4, 1, hbuf);
    
    snprintf(abuf, sizeof(abuf),
      "{\"id\":\"%s\",\"src\":\"esp32_flame\",\"alert\":\"flame\",\"t\":%s,\"h\":%s,"
      "\"gasA\":%d,\"gasMv\":%lu}",
      chipIdString().c_str(), tbuf, hbuf, gasAnalog, (unsigned long)gasMv);
    
    mqtt.publish(TOPIC_ALERT, abuf, false);
    mqtt.publish(TOPIC_EVENT, "{\"event\":\"flame_on\"}", false);
    Serial.println("[ALERT] Flame detected!");
  }
  prevFlame = flameTrig;

  // LCD refresh tiap 1 detik
  static unsigned long lastLcd = 0;
  if (millis() - lastLcd >= 1000) {
    lastLcd = millis();
    char l1[17], l2[17];
    
    if (isnan(t) || isnan(h)) 
      snprintf(l1, sizeof(l1), "T: --.-C H:--%%");
    else 
      snprintf(l1, sizeof(l1), "T:%4.1fC H:%2.0f%%", t, h);
    
    const char* alarmSrc = "";
    if (fire) {
      if (forceAlarm) alarmSrc = "YOL";
      else if (flameTrig) alarmSrc = "FLM";
      else alarmSrc = "GAS";
    }
    
    snprintf(l2, sizeof(l2), "G:%4d F:%s %s%s",
             gasAnalog, 
             flameTrig ? "ON " : "OFF", 
             fire ? "ALRM" : "OK  ",
             fire ? alarmSrc : "");
    
    lcdPrint2(l1, l2);
  }

  // Telemetry tiap 30 detik
  if (millis() - lastPub >= PUB_MS) {
    lastPub = millis();

    char tbuf[8], hbuf[8];
    if (isnan(t)) snprintf(tbuf, sizeof(tbuf), "null"); 
    else dtostrf(t, 4, 1, tbuf);
    if (isnan(h)) snprintf(hbuf, sizeof(hbuf), "null"); 
    else dtostrf(h, 4, 1, hbuf);

    char payload[280];
    snprintf(payload, sizeof(payload),
      "{\"id\":\"%s\",\"t\":%s,\"h\":%s,\"gasA\":%d,\"gasMv\":%lu,"
      "\"gasD\":%s,\"flame\":%s,\"alarm\":%s,\"forceAlarm\":%s}",
      chipIdString().c_str(),
      tbuf, hbuf,
      gasAnalog, (unsigned long)gasMv,
      gasTrig ? "true" : "false",
      flameTrig ? "true" : "false",
      fire ? "true" : "false",
      forceAlarm ? "true" : "false");

    mqtt.publish(TOPIC_PUB, payload);
    mqtt.publish(TOPIC_LOG, payload);
    Serial.printf("[TELEMETRY] %s\n", payload);
  }

  delay(100);
}
