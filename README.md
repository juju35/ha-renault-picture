# ha-renault-picture

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![HACS Validation](https://github.com/juju35/ha-renault-picture/actions/workflows/hacs.yml/badge.svg)](https://github.com/juju35/ha-renault-picture/actions/workflows/hacs.yml)
[![Validate](https://github.com/juju35/ha-renault-picture/actions/workflows/validate.yml/badge.svg)](https://github.com/juju35/ha-renault-picture/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/juju35/ha-renault-picture)](https://github.com/juju35/ha-renault-picture/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Home Assistant integration that exposes the **official MyRenault vehicle picture**
as a sensor, for every car handled by the core [`renault`](https://www.home-assistant.io/integrations/renault/) integration.

The picture URL already lives in the data the `renault` integration loads from
Kamereon (each vehicle's `PICTURE` asset). This integration only reads it and
publishes it, so it needs **no credentials** and makes **no network calls** of its own.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=juju35&repository=ha-renault-picture&category=integration)

## Features

- One `sensor.<vehicle>_picture` per vehicle, attached to the existing Renault device
- The official picture URL as `entity_picture` (shown as the entity thumbnail) and in attributes
- No credentials, no extra API calls: the data comes from the `renault` integration already running
- English and French

## Prerequisites

- Home Assistant 2025.8 or later
- The core [`renault`](https://www.home-assistant.io/integrations/renault/) integration configured and loaded

## Installation

### Via HACS (recommended)

Click the button below to add the repository directly:

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=juju35&repository=ha-renault-picture&category=integration)

Then click **Download** and restart Home Assistant.

Or manually:

1. Open HACS → **⋮** (top right) → **Custom repositories**
2. Add `https://github.com/juju35/ha-renault-picture` — Type: **Integration**
3. Search for **Renault Picture** and click **Download**
4. Restart Home Assistant

### Manual

Copy `custom_components/renault_picture/` to `/config/custom_components/renault_picture/`, then restart Home Assistant.

## Configuration

[![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=renault_picture)

**Settings → Devices & services → Add integration → Renault Picture**. There is nothing to fill in; it finds the vehicles from the Renault integration.

### Entity

One sensor per vehicle, attached to the existing Renault device:

| | |
|---|---|
| `state` | `available` / `no_picture` (kept short; a picture URL is too long for a state, and `no_picture` stays distinguishable from Home Assistant's own `unavailable`) |
| `entity_picture` | the large picture URL — shown as the entity thumbnail |
| attribute `picture_large` | large render URL |
| attribute `picture_small` | thumbnail render URL |
| attribute `available_renditions` | raw Kamereon assets, for troubleshooting |
| attribute `vin` | the vehicle VIN |

## Use with ha-renault-card

[ha-renault-card](https://github.com/juju35/ha-renault-card) picks the picture up automatically: it finds this integration's sensor on the vehicle's device and uses its `picture_large` URL. Leave the card's `image` option empty; set it only to override the MyRenault photo with a plain URL (the option does not render templates):

```yaml
type: custom:renault-card
image: /local/renault/clio.png
```

## How it works

The core `renault` integration loads each vehicle's details from Kamereon, which
include a `PICTURE` asset with `ONE_MYRENAULT_LARGE` and `ONE_MYRENAULT_SMALL`
renditions. This integration reads those straight from the loaded data
(`entry.runtime_data`), so it adds no API calls and needs no credentials. If a
future Renault or HACS change moves that data, the sensor reports `unavailable`
instead of breaking, and `available_renditions` shows what the car actually exposes.

To debug:

```yaml
logger:
  logs:
    custom_components.renault_picture: debug
```

## Development

```bash
pip install -r requirements_test.txt && pytest
```

### Releasing

1. Bump the version in `custom_components/renault_picture/manifest.json`
2. Add a `## <version>` section at the top of [CHANGELOG.md](CHANGELOG.md)
3. Push to `main`: the **Release** workflow creates the tag and the GitHub release with the changelog section as notes

## Translations

The integration follows the language of Home Assistant. Currently supported:

| Language | Code |
|---|---|
| English | `en` |
| Français | `fr` |

## License

[MIT](LICENSE)

Not affiliated with Renault.
