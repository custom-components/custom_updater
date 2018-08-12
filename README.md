# Custom Updater

A component which allows you to track and update your custom cards and components.\
**To get the best use for this component, use it together with the [tracker-card](https://github.com/custom-cards/tracker-card)**

## Installation

### Step 1

Install this component by copying `/custom_components/custom_updater.py` from this repo to `<config directory>/custom_components/custom_updater.py` on your Home Assistant instanse.

### Step 2

Add this to your `configuration.yaml`

```yaml
custom_updater:
```

### Optional config options

| key | default | required | description
| --- | --- | --- | ---
| **track** | both | no | A list of what you want this component to track, possible values are `cards`/`components`.
| **hide_sensor** | False | no | Option to set the sensors to be `hidden`, possible values are `True` / `False`.
| **card_urls** | Empty | no | A list of additional urls to json with card info.
| **component_urls** | Empty | no | A list of additional urls to json with component info.

The component uses these json files to check for updates by default:

- https://raw.githubusercontent.com/custom-cards/information/master/repos.json
- https://raw.githubusercontent.com/custom-components/information/master/repos.json

Use the `card_urls` and `component_urls` options in the configuration to add more.

***

### Format of card_urls json

The json can have multiple cards

```json
{
    "canvas-gauge-card": {
      "updated_at": "2018-08-11",
      "version": "0.0.2",
      "remote_location": "https://raw.githubusercontent.com/custom-cards/canvas-gauge-card/master/canvas-gauge-card.js",
      "visit_repo": "https://github.com/custom-cards/canvas-gauge-card",
      "changelog": "https://github.com/custom-cards/canvas-gauge-card/releases/latest"
    }
}
```

### Format of component_urls json

The json can have multiple components

```json
{
    "camera.combined": {
      "updated_at": "2018-08-08",
      "version": "0.0.1",
      "local_location": "/custom_components/camera/combined.py",
      "remote_location": "https://raw.githubusercontent.com/custom-components/camera.combined/master/custom_components/camera/combined.py",
      "visit_repo": "https://github.com/custom-components/camera.combined",
      "changelog": "https://github.com/custom-components/camera.combined/releases/latest"
    }
}
```

## Activate Debug logging

Put this in your `configuration.yaml`

```yaml
logger:
  default: warn
  logs:
    custom_components.custom_updater: debug
```

***

## Services

If you are not using the Lovelace UI or **our recommended [tracker-card](https://github.com/custom-cards/tracker-card)** for it,\
you can still update custom-cards and -components by calling services from dev-service.

### Check for updates

Service: `custom_updater.check_all`

### Update all

Service: `custom_updater.update_all`

### Update single card

You can update a single card by passing which card you want to update to the `custom_updater.upgrade_single_card` service.

Service: `custom_updater.upgrade_single_card`

Service Data:

```json
{
  "card":"monster-card"
}
```

### Update single component

You can update a single component by passing which component you want to update to the  `custom_updater.upgrade_single_component` service.

Service: `custom_updater.upgrade_single_component`

Service Data:

```json
{
  "component":"sensor.authenticated"
}
```
