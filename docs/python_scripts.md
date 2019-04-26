This component can also be used to track your python_scripts, for this to be possible you need to host a json file in your repo that your users can add to this component, you also need to add a local version tag inside the `.py` file, the supported format for this are `VERSION = 'x.y.z'`.

**Format example for json file:**

```json
{
    "light_control": {
      "version": "0.0.7",
      "local_location": "python_scripts/light_control.py",
      "remote_location": "https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/python_scripts/light_control.py",
      "visit_repo": "https://github.com/awesome-developer/my-awesome-repo",
      "changelog": "https://github.com/awesome-developer/my-awesome-repo/releases/latest"
    },
    "notifier": {
      "version": "1.2.7",
      "local_location": "python_scripts/notifier.py",
      "remote_location": "https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/custom_components/notifier.py",
      "visit_repo": "https://github.com/awesome-developer/my-awesome-repo",
      "changelog": "https://github.com/awesome-developer/my-awesome-repo/releases/latest"
    }
}
```
**NB!: All the keys in this example must be present in the file!**

***

The user needs to add the raw file to the component under the optional option `python_script_urls`
configuration example:
```yaml
custom_updater:
  track:
    - python_scripts
  python_script_urls:
    - https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/python_scripts.json
```