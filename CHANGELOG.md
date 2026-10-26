# Changelog

## 0.1.0

### Features
- Initial release. One `sensor.<vehicle>_picture` per Renault vehicle, exposing the official MyRenault picture URL. The URL already lives in the data the core `renault` integration loads from Kamereon, so this integration reuses it: no credentials and no network calls of its own.
- The URL is published as the sensor's `entity_picture` (shown as the entity thumbnail) and in the `picture_large` / `picture_small` attributes; the state is kept short (`available` / `unavailable`) because a URL is too long for a state.
- The `available_renditions` attribute lists the raw Kamereon assets, for troubleshooting.
- English and French.
