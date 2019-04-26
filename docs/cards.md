This component can also be used to track your cards, for this to be possible you need to host a json file in your repo that your users can add to this component.

For cards that the user already have installed, it checks the `ui-lovelace.yaml` file or `.storage/lovelace`, example for `awesome-card1.js`:
```yaml
resources:
  - url: /customcards/awesome-card1.js
    type: js
```

**Format example for json file:**

```json
{
    "awesome-card1": {
      "version": "0.0.7",
      "remote_location": "https://raw.githubusercontent.com/my-awesome-repo/awesome-card1/master/awesome-card1.js",
      "visit_repo": "https://github.com/my-awesome-repo/awesome-card1",
      "changelog": "https://github.com/my-awesome-repo/awesome-card1/releases/latest"
    },
    "awesome-card2": {
      "version": "1.2.3",
      "remote_location": "https://raw.githubusercontent.com/my-awesome-repo/awesome-card2/master/awesome-card2.js",
      "visit_repo": "https://github.com/my-awesome-repo/awesome-card2",
      "changelog": "https://github.com/my-awesome-repo/awesome-card2/releases/latest"
    }
}
```
**NB!: All the keys in this example must be present in the file!**

***

The user needs to add the raw file to the component under the optional option `card_urls`
configuration example:
```yaml
custom_updater:
  track:
    - cards
  card_urls:
    - https://raw.githubusercontent.com/awesome-developer/my-awesome-repo/master/custom_cards.json
```