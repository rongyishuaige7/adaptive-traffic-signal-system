.PHONY: verify test frontend firmware clean
verify:
	bash scripts/verify.sh

test:
	VIDEO_WORKERS_ENABLED=false SIGNAL_ENGINE_ENABLED=false python3 -m pytest tests -q

frontend:
	cd frontend && npm ci && npm run build

firmware:
	PLATFORMIO_BUILD_FLAGS='-DWIFI_SSID=\"LOCAL_TEST_SSID\" -DWIFI_PASS=\"LOCAL_TEST_PASSWORD\"' pio run -d firmware/esp32_cam
	PLATFORMIO_BUILD_FLAGS='-DWIFI_SSID=\"LOCAL_TEST_SSID\" -DWIFI_PASS=\"LOCAL_TEST_PASSWORD\" -DPC_HOST=\"127.0.0.1\"' pio run -d firmware/esp32_main

clean:
	rm -rf frontend/node_modules frontend/dist firmware/esp32_cam/.pio firmware/esp32_main/.pio .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
