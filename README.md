# ha-renault-picture

[![Marketplace](https://img.shields.io/badge/Marketplace-Custom-41BDF5.svg)](https://www.home-assistant.io/integrations/marketplace/)
[![HACS Validation](https://github.com/juju35/ha-renault-picture/actions/workflows/hacs.yml/badge.svg)](https://github.com/juju35/ha-renault-picture/actions/workflows/hacs.yml)
[![Validate](https://github.com/juju35/ha-renault-picture/actions/workflows/validate.yml/badge.svg)](https://github.com/juju35/ha-renault-picture/actions/workflows/validate.yml)
[![Lint](https://github.com/juju35/ha-renault-picture/actions/workflows/lint.yml/badge.svg)](https://github.com/juju35/ha-renault-picture/actions/workflows/lint.yml)
[![Release](https://img.shields.io/github/v/release/juju35/ha-renault-picture)](https://github.com/juju35/ha-renault-picture/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/juju35/ha-renault-picture/blob/main/LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/julienstep9)

Home Assistant integration that exposes the **official MyRenault vehicle picture**
as a sensor, for every car handled by the core [`renault`](https://www.home-assistant.io/integrations/renault/) integration.

The picture URL already lives in the data the `renault` integration loads from
Kamereon (each vehicle's `PICTURE` asset). This integration only reads it and
publishes it, so it needs **no credentials** and makes **no network calls** of its own.

[![Open your Home Assistant instance and open a repository inside the Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=juju35&repository=ha-renault-picture&category=integration)

## Features

- One `sensor.<vehicle>_picture` per vehicle, attached to the existing Renault device
- The official picture URL as `entity_picture` (shown as the entity thumbnail) and in attributes
- No credentials, no extra API calls: the data comes from the `renault` integration already running
- English, French, German, Spanish, Serbian (Cyrillic and Latin), Italian, Dutch, Portuguese (European and Brazilian), Polish, Romanian, Danish, Swedish, Bulgarian, Russian, Ukrainian, Hungarian, Slovak, Czech, Slovenian, Latvian and Greek

## Supported integrations

| Integration | What it reads |
|---|---|
| [Renault](https://www.home-assistant.io/integrations/renault/) (built in) | The vehicle details the integration already fetched (no extra API calls, no credentials), to expose the official MyRenault picture of each vehicle |

The picture is shown by [Renault Card](https://github.com/juju35/ha-renault-card), see [Use with ha-renault-card](#use-with-ha-renault-card).

## Prerequisites

- Home Assistant 2025.8 or later
- The core [`renault`](https://www.home-assistant.io/integrations/renault/) integration configured and loaded

## Installation

### Via the Marketplace (recommended)

Click the button below to add the repository directly:

[![Add to the Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=juju35&repository=ha-renault-picture&category=integration)

Then click **Install** and restart Home Assistant.

Or manually:

1. Open **Settings → Marketplace → Add from link** (top right; this needs a GitHub account connected)
2. Add `https://github.com/juju35/ha-renault-picture` — Type: **Integration**
3. Open **Renault Picture** and click **Install**
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
| attribute `vin` | the vehicle VIN (not recorded in the history) |

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
future change of the Home Assistant `renault` integration moves the picture
assets, the sensor reports `no_picture` instead of breaking, and
`available_renditions` shows what the car actually exposes. While no `renault`
entry is loaded with vehicles (startup, reauth, integration removed), the entry
shows **Retrying setup** and Home Assistant retries it on its own.

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
2. Add a `## <version>` section at the top of [CHANGELOG.md](https://github.com/juju35/ha-renault-picture/blob/main/CHANGELOG.md)
3. Push to `main`: the **Release** workflow creates the tag and the GitHub release with the changelog section as notes

## Translations

The integration follows the language of Home Assistant. Currently supported:

| Language | Code |
|---|---|
| English | `en` |
| Français | `fr` |
| Deutsch | `de` |
| Español | `es` |
| Српски | `sr` |
| Srpski (latinica) | `sr-Latn` |
| Italiano | `it` |
| Nederlands | `nl` |
| Português | `pt` |
| Português (Brasil) | `pt-BR` |
| Polski | `pl` |
| Română | `ro` |
| Dansk | `da` |
| Svenska | `sv` |
| Български | `bg` |
| Русский | `ru` |
| Українська | `uk` |
| Magyar | `hu` |
| Slovenčina | `sk` |
| Čeština | `cs` |
| Slovenščina | `sl` |
| Latviešu | `lv` |
| Ελληνικά | `el` |

## License

[MIT](https://github.com/juju35/ha-renault-picture/blob/main/LICENSE)

Not affiliated with Renault.

## Support

If you find this project useful, you can support its development:

<a href="https://buymeacoffee.com/julienstep9"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" height="50"></a>
