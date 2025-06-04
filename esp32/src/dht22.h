#include "DHTesp.h"
#include <Ticker.h>
#include <ArduinoJson.h>
#include <ezTime.h>
#include "ESPRandom.h"   // UUID creation


DHTesp dht;

String get_dht22_data(int dhtpin) {
    dht.setup(dhtpin, DHTesp::DHT22);
    Serial.println("DHT initiated");
    // Serial.println(dht.getStatus());

    waitForSync(); // Pause until time is successfully updated
    DynamicJsonDocument doc(1024);
    // Create random uuid
    uint8_t uuid[16];
    ESPRandom::uuid(uuid);
    doc["device_id"] = DEVICE_ID;
    doc["uuid"] = ESPRandom::uuidToString(uuid);
    doc["time"] = UTC.dateTime(RFC3339);
    doc["temperature"] = dht.getTemperature();
    doc["humidity"] = dht.getHumidity();
    //doc["temperature"] = String(dht.getTemperature());
    //doc["humidity"] = String(dht.getHumidity());
    std::string serial;
    serializeJson(doc, serial);
    return serial.c_str();
}
