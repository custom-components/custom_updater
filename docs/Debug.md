# Activate Debug logging

Put this in your `configuration.yaml`

```yaml
logger: # https://www.home-assistant.io/components/logger/
  default: error
  logs:
    custom_components.custom_updater: debug
    pyupdate: debug
```