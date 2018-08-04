# Custom Updater

A component which allows you to track and update your custom cards and components.\
**To get the best use for this component, use it together with the [tracker-card](https://github.com/custom-cards/tracker-card)**

## ⚠️ This will **ONLY** work if your components and/or cards/elements is from

- https://github.com/custom-cards
- https://github.com/custom-components
- https://github.com/ciotlosm/custom-lovelace

***

## ⚠️ See here **if** you have used an earlier version of this

Before  you install this version make sure that you remove these files (if you have them):

- `/custom_components/custom_components.py`
- `/custom_components/custom_cards.py`
- `/custom_components/sensor/custom_components.py`
- `/custom_components/sensor/custom_cards.py`

And remove `custom_components` and `custom_cards` from your `configuration.yaml`

***

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
| **track** | both | no | A list of what you want this component to track, possible values are `cards`/`components`
| **hide_sensor** | False | no | Option to set the sensors to be `hidden`, possible values are `True` / `False`

***

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
