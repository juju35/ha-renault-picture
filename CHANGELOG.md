# Changelog

## 0.2.0

### Changes
- Minimum Home Assistant raised to 2025.8: attaching the picture sensor to the vehicle's Renault device needs it (on older versions the sensor registered without a device).
- The sensor state is now an enum, `available` / `no_picture` (translated in English and French), instead of the literal `unavailable`, which could not be told apart from Home Assistant's own unavailable state. Update automations that tested `unavailable`.
- The picture URLs are computed once and the sensor is no longer polled; `picture_large`, `picture_small` and `available_renditions` are no longer recorded in the history.
- HACS now installs the release zip instead of downloading the repository.

### Fixes
- The sensors are created even when the Renault integration is not loaded yet at startup (the platform setup is retried instead of giving up until a restart).
- The integration reloads when a Renault config entry reloads or is removed, so the sensors no longer point at a stale hub and newly added vehicles show up.
- The config flow refuses to create an entry until a Renault entry is loaded with vehicles, instead of creating one that produced no sensor.
- Debug logs now show the number of sensors and vehicles without a picture.
- README: the ha-renault-card example reflects the card's actual behaviour.

## 0.1.1

### Fixes
- The picture sensor now joins the vehicle's Renault device and is named after it ("Espace Picture"), instead of creating a separate "Renault Picture" device per vehicle. Home Assistant no longer treats device identifiers as unique across integrations, so the sensor is now linked to the Renault device directly.
- The "Renault Picture" devices created by 0.1.0 are removed at startup.
- README: the top button adds the repository to HACS (it started the config flow, which fails before the download).

## 0.1.0

### Features
- Initial release. One `sensor.<vehicle>_picture` per Renault vehicle, exposing the official MyRenault picture URL. The URL already lives in the data the core `renault` integration loads from Kamereon, so this integration reuses it: no credentials and no network calls of its own.
- The URL is published as the sensor's `entity_picture` (shown as the entity thumbnail) and in the `picture_large` / `picture_small` attributes; the state is kept short (`available` / `unavailable`) because a URL is too long for a state.
- The `available_renditions` attribute lists the raw Kamereon assets, for troubleshooting.
- English and French.
