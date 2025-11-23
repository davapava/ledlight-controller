# LED Light Controller Skeleton

Detta repo innehåller ett minimalt skelett för en tjänst som läser dagsljus från en webbkamera och uppdaterar en Wi-Fi RGB-lampa. Ingen funktionell implementation är inkluderad ännu – fokus ligger på strukturen och de abstrakta komponenterna.

## Projektlayout

```
src/
  ledlight_controller/
    __init__.py
    camera_client.py
    config.py
    light_client.py
    main.py
    models.py
    pipeline.py
    service.py
```

## Arkitekturöversikt

 - `camera_client.py` beskriver gränssnittet mot webbkameran och en placeholder för en OpenCV-baserad implementation.
 - `light_client.py` definierar ett abstrakt gränssnitt för att prata med en Wi-Fi-lampa och ett enkelt Yeelight-inspirerat skelett.
 - `image_analysis.py` läser in stillbilder och räknar fram medelluminans och RGB-fördelning.
 - `pipeline.py` håller logiken för att översätta ljusmätningar till RGB-färger.
 - `service.py` orkestrerar händelseflödet: läs kamera, mappa färg, uppdatera lampan.

## Nästa steg

1. Implementera en konkret `CameraReader` som använder OpenCV för att läsa bildrutor och extrahera ljusnivå.
2. Fyll i `ColorMapper` med en strategi som översätter lux till RGB.
3. Implementera en `LampController` som pratar med vald Wi-Fi-lampa (t.ex. Yeelight).
4. Koppla ihop allt i `build_default_app()` i `main.py`.
5. Lägg till tester och eventuella konfigurationsfiler.

## Hjälpskript

- `ledlight-controller-tapo-capture` pollar en Tapo C100 RTSP-ström via `ffmpeg`, analyserar varje bildruta och loggar medelluminans samt RGB-sammanfattning var 20:e sekund (standard). Exempel:

  ```bash
  python -m ledlight_controller.scripts.tapo_capture_loop --rtsp-url "rtsp://user:pass@192.168.68.68:554/stream1"
  ```

  Standardvärden för `rtsp_url`, `interval_seconds` och `timeout_seconds` hämtas från `config/settings.toml` (`[tapo_capture]`-sektionen). Varje värde kan överskridas via motsvarande CLI-flagga.
- `ledlight-controller-tuya-color` läser Tuya-konfigurationen ur `config/settings.toml` och skickar en RGB-färg till lampan med hjälp av `tinytuya`. Exempel:

  ```bash
  python -m ledlight_controller.scripts.tuya_color_test --hex ff8800
  ```

  Du kan använda `--rgb 255 136 0` om du hellre anger tre kanaler direkt.

## Bildanalys

Modulen `image_analysis.py` innehåller hjälpfunktioner som plockar ut medelluminans och färgkanaler från en bildruta. Exempel på användning:

```python
from pathlib import Path
from ledlight_controller.image_analysis import analyse_image

stats = analyse_image(Path("/tmp/tapo_snapshot.jpg"))
print(stats.measurement.normalized)
print(stats.average_color)
```

Den kräver att `numpy` och `opencv-python` (eller systempaketet `python3-opencv`) finns installerade.

## Lampkonfiguration (Tuya)

1. Skapa ett Tuya IoT Cloud-projekt och koppla din V-TAC-lampa (ofta Tuya-baserad). Dokumentation finns i [tinytuya-guiden](https://github.com/jasonacox/tinytuya#tuya-cloud-project).
2. Hämta `device_id`, `local_key` och IP-adressen (`address`) för lampan och fyll i dem i `config/settings.toml` under `[lamp]`.
3. Installera `tinytuya` i din miljö (`pip install tinytuya`).
4. Testa anslutningen med `ledlight-controller-tuya-color` innan du kopplar mappningen till själva tjänsten.
