# Changelog

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
