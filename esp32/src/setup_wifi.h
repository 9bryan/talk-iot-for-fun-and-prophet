#include <WiFiManager.h>

void setup_wifi() {
    WiFi.mode(WIFI_STA);
    WiFiManager wm;

    Serial.println("Starting WiFi setup...");
    Serial.print("SSID: "); Serial.println(WIFI_SSID);

    wm.setConfigPortalTimeout(30); // prevent permanent AP mode during failure
    // wm.resetSettings(); // use once to clear flash if needed

    bool res = wm.autoConnect(WIFI_SSID, WIFI_PASSWORD);

    if (!res) {
        Serial.println("[WiFiManager] Failed to connect. Restarting...");
        delay(2000);
        ESP.restart();
    } else {
        Serial.println("[WiFiManager] Connected to WiFi!");
    }
}
