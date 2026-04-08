#ifndef ARDUINO_INKPLATE2
#error "Wrong board selection for this example, please select Soldered Inkplate2 in the boards menu."
#endif

#include "Inkplate.h"
#include <WiFi.h>
#include <HTTPClient.h>

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const char *WIFI_SSID     = "Lord_Voldemodem-EXT";
const char *WIFI_PASSWORD = "aquariumawardremembereconomist";
const char *IMAGE_URL     = "http://192.168.1.55/today.png";

// Deep sleep interval in microseconds (default: 24 hours)
const uint64_t SLEEP_INTERVAL_US = 24ULL * 60 * 60 * 1000 * 1000;

// ---------------------------------------------------------------------------

Inkplate display;

void setup()
{
    Serial.begin(115200);
    display.begin();

    // Connect to WiFi
    Serial.print("Connecting to WiFi");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" connected.");

    // Fetch and display the image
    Serial.println("Downloading image...");
    if (!display.drawImage(IMAGE_URL, 0, 0, false, false))
    {
        display.clearDisplay();
        display.println("Image load error");
        Serial.println("Image load error.");
    }
    display.display();

    // Shut down WiFi before sleeping
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);

    // Deep sleep
    Serial.println("Going to sleep.");
    delay(100);
    esp_sleep_enable_timer_wakeup(SLEEP_INTERVAL_US);
    esp_deep_sleep_start();
}

void loop()
{
    // Never reached; deep sleep restarts the sketch from setup().
}
