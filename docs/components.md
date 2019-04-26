This component can also be used to track your components/platforms, for this to be possible you need to host a json file in your repo that your users can add to this component, you also need to add a local version tag inside the `.py` file

## Version tags
For platforms(single file), you need to put the tag inside the .py file.
For component (from version `4.2.14`) you can import it from another file ex. `const.py`, example:

```python
from custom_components.mail_daemon.const import VERSION
```

```python
from .const import VERSION
```

### Supported tag formats

```python
VERSION = 'x.y.z'
```

```python
__version__ = 'x.y.z'
```

## JSON file examples

The "name" (main key) of the platform should be in the `domain.name` format, like `camera.combined` in the example below.

**Format example for json file:**

```json
{
    "camera.combined": {
        "version": "0.0.7",
        "local_location": "/custom_components/combined/camera.py",
        "remote_location": "https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/custom_components/combined/camera.py",
        "visit_repo": "https://github.com/awesome-developer/my-awesome-repo",
        "changelog": "https://github.com/awesome-developer/my-awesome-repo/releases/latest"
    },
    "mail_daemon": {
        "version": "0.0.7",
        "local_location": "/custom_components/mail_daemon/__init__.py",
        "remote_location": "https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/custom_components/mail_daemon/__init__.py",
        "visit_repo": "https://github.com/awesome-developer/my-awesome-repo",
        "changelog": "https://github.com/awesome-developer/my-awesome-repo/releases/latest",
        "resources": [
            "https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/custom_components/mail_daemon/const.py",
            "https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/custom_components/mail_daemon/services.yaml"
        ]
    }
}
```
**NB!: All the keys in this example must be present in the file!**

***

The user needs to add the raw file to the component under the optional option `component_urls`
configuration example:
```yaml
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/custom_components.json
```

## Extra resources

The components of today are no longer just a single file, from version `4.2.11` additional resources can be downloaded (if defined in the json file).

_See the `mail_daemon` example above on how to include the `resources` key_

For this to work the component need to be in it's own directory and be named `__init__.py` on the `local_location` key, example:

```text
"local_location": "/custom_components/mail_daemon/__init__.py",
```

Additional resources from the `resources` key will be downloaded to the same dir as this component.
The result of the example for `mail_daemon` will be:

```text
custom_components/mail_daemon/__init__.py
custom_components/mail_daemon/const.py
custom_components/mail_daemon/services.yaml
```