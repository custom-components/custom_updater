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
| **track** | `cards`, `components` | no | A list of what you want this component to track, possible values are `cards`/`components`

***

## Activate Debug logging

Put this in your `configuration.yaml`

```yaml
logger:
  default: warn
  logs:
    custom_components.custom_updater: debug
```
