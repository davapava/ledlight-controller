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
- `pipeline.py` håller logiken för att översätta ljusmätningar till RGB-färger.
- `service.py` orkestrerar händelseflödet: läs kamera, mappa färg, uppdatera lampan.
- `main.py` kommer i framtiden att binda ihop komponenterna och exponera ett CLI.

## Nästa steg

1. Implementera en konkret `CameraReader` som använder OpenCV för att läsa bildrutor och extrahera ljusnivå.
2. Fyll i `ColorMapper` med en strategi som översätter lux till RGB.
3. Implementera en `LampController` som pratar med vald Wi-Fi-lampa (t.ex. Yeelight).
4. Koppla ihop allt i `build_default_app()` i `main.py`.
5. Lägg till tester och eventuella konfigurationsfiler.

## Hjälpskript

- `ledlight-controller-tapo-capture` pollar en Tapo C100 RTSP-ström via `ffmpeg` och tar en stillbild var 20:e sekund (standard). Exempel:

  ```bash
  python -m ledlight_controller.scripts.tapo_capture_loop --rtsp-url "rtsp://user:pass@192.168.68.68:554/stream1"
  ```
