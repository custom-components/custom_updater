# Check for updates

Service: `custom_updater.check_all`  
This will check for updates for all tracked elements.

# Update all

Service: `custom_updater.update_all`  
This will update all tracked elements that you have installed if there is an update for them.

# Install element (card/component/python_script)

Service: `custom_updater.install`

Service Data:

```json
{
  "element":"sensor.authenticated"
}
```

This will install the element, but you will still need to enable it in your configuration.