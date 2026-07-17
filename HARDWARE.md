# Hardware and wiring boundary

This is a **source-derived connection guide**, not an EDA schematic and not proof that the retained five-board assembly was re-tested on the current public commit.

## ESP32 main controller

| Direction | Red | Yellow | Green |
|:--|:--|:--|:--|
| North | GPIO13 | GPIO14 | GPIO27 |
| South | GPIO16 | GPIO17 | GPIO18 |
| East | GPIO19 | GPIO21 | GPIO22 |
| West | GPIO23 | GPIO25 | GPIO26 |

The source assumes four three-color modules with built-in current limiting. Confirm the real module voltage, polarity and resistor values before wiring. GPIO14 is a strapping pin. GPIO16/17 are unavailable on some ESP32-WROVER boards with PSRAM, so the exact controller module must be physically confirmed.

## Four OLEDs through TCA9548A

| Function | Main ESP32 / multiplexer |
|:--|:--|
| SDA | GPIO4 |
| SCL | GPIO5 |
| TCA9548A address | `0x70`, A0/A1/A2 low |
| North OLED | channel 0, SSD1306 `0x3C` |
| South OLED | channel 1, SSD1306 `0x3C` |
| East OLED | channel 2, SSD1306 `0x3C` |
| West OLED | channel 3, SSD1306 `0x3C` |

## ESP32-CAM nodes

The firmware uses the AI Thinker camera pin map and provides `/`, `/jpg` and `/stream`. N/S/E/W builds differ only by `CAM_DIRECTION`; DHCP is the public default. Wi-Fi and optional static addressing are local, ignored configuration.

Use a stable supply appropriate for the exact ESP32-CAM boards; the historical guide recommends 5 V / 1 A for each node. All control/display modules share a common reference ground where their power topology requires it.

## Confirm before upgrading the evidence status

- exact ESP32 main and four ESP32-CAM module revisions;
- exact camera sensors;
- display and multiplexer modules;
- traffic-light module voltage, polarity and resistor values;
- actual power rails and common-ground topology;
- current wiring against every GPIO above;
- whether the all-red disconnect behavior is observable on real LEDs.

See [the wiring boundary diagram](hardware/wiring-diagram.svg) and [BOM](hardware/BOM.csv).
