If you are upgrading from a previous version of custom_updater, DELETE `<config directory>/custom_components/custom_updater.py` file on your Home Assistant instance.

# Step 1

Create a directory called `custom_updater` in the `<config directory>/custom_components/` directory on your Home Assistant instance.
Install this component by copying the files in [`/custom_components/custom_updater/`](https://raw.githubusercontent.com/custom-components/custom_updater/master/custom_components/custom_updater/__init__.py and https://raw.githubusercontent.com/custom-components/custom_updater/master/custom_components/custom_updater/services.yaml) from this repo into the new `<config directory>/custom_components/custom_updater/` directory you just created

# Step 2

Add this to your `configuration.yaml`

```yaml
custom_updater:
```

# Optional config options
This is all the optional configuration options for this component.  

## Configuration option: `track`
**default value:** `components`, `cards`  
**type:** List  
**description:**  
A list of what you want this component to track, possible values are:

- `cards`
- `components`
- `python_scripts`

## Configuration option: `hide_sensor`
**default value:** `False`  
**type:** boolean  
**description:**  
Option to set the sensors to be `hidden`, possible values are `True` / `False`.


## Configuration option: `show_installable`
**default value:** `False`  
**type:** boolean  
**description:**  
Option show installable components/cards, possible values are `True` / `False`.  
This will show **all** elements from every source you are tracking.

__Not in use__

## Configuration option: `card_urls`
**default value:** None  
**type:** list  
**description:**  
A list of additional URLs to json with card info.  

_This part are considered advanced configuration, this option is here to provide support for third-party cards, **do not** add anything here unless a card dev has made a special json file for this you can point to, putting in a URL directly to a card here will **not** work, and can potentially cause the component to fail._

## Configuration option: `component_urls`
**default value:** None  
**type:** list  
**description:**  
A list of additional urls to json with card info.  

_This part are considered advanced configuration, this option is here to provide support for third-party components, **do not** add anything here unless a component dev has made a special json file for this you can point to, putting in a URL directly to a card here will **not** work, and can potentially cause the component to fail._

## Configuration option: `python_script_urls`
**default value:** None  
**type:** list  
**description:**  
A list of additional urls to json with python_script info.  

_This part are considered advanced configuration, this option is here to provide support for third-party python_script, **do not** add anything here unless a python_script dev has made a special json file for this you can point to, putting in a URL directly to a card here will **not** work, and can potentially cause the component to fail._



### Config validation

Home Assistant will fail configuration validation the first time after you add this, this is because it does not know of it and it's capabilities (config options)

see the [How it works page of this wiki](https://custom-components.github.io/custom_updater/How-it-works) for details on how to set up your custom elements.
