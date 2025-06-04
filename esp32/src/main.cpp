#include <Arduino.h>
#include "config.h"
#include "setup_wifi.h"
#include "deep_sleep_and_restart.h"
#include "dht22.h"
#include "mqtt.h"
#include <ezTime.h>

void setup() {
    Serial.begin(9600);
    delay(1500);

    Serial.print(PSTR("[Device][setup] - Starting, free heap: "));
    Serial.println(ESP.getFreeHeap());

    setup_wifi();
    delay(500);
    
    waitForSync();  // Sync NTP time
    Serial.println("UTC: " + UTC.dateTime(RFC3339));
    delay(500);

    String payload = get_dht22_data(4);
    Serial.println("[Device] Payload: " + payload);

    // Connect to AWS IoT MQTT
    connect_mqtt();
    delay(500);  // Allow time for connection

    // Construct dynamic topic based on DEVICE_ID
    String topic = "environment-data/";
    topic += DEVICE_ID;
    Serial.println("[MQTT] Publishing to topic: " + topic);

    // Publish sensor data
    publish_mqtt(topic, payload);

    // Sleep for 60 seconds
    deep_sleep_and_restart(300);
}

void loop() {
    // Not used
}
