_`super_custom` cards is a new concept that was added in version 4.2.something._

**Note: Not all custom cards are supported with this, it's up to the developer to add support for the card.**

This new concept makes it really easy to install new custom_cards, and will also open up for even more card support.  
As with everything else, there are some "rules" to make this work.

## Installation demo with "super_custom"

![demo](https://github.com/custom-cards/tracker-card/blob/master/files/tracker-card.gif)

## The user

All you as the user needs to do to get the card is to folow the developers instructions, you usually find them in a readme file in the repo.

If the "url" in the example for `resources` are like this it's configured for "super_custom":

```text
url: /customcards/github/my-awesome-repo/awesome-card.js?track=true
```

_Note: It starts with `/customcards/github/` then the developers username, then the card name, then ends with `?track=true`_

## The developer

As a developer to take advantage of this:

- Your card must be hosted on GitHub.
- The card-name and repo-name must be identical.
- In the root of the repo there must be a .json (manifest) file with one of these names:
  - custom_card.json
  - tracker.json
  - updater.json
  - custom_updater.json

_The json file can **only** contain data about one card._

### Example for the content of that json file:

```json
{
    "awesome-card": {
      "version": "0.0.7",
      "remote_location": "https://raw.githubusercontent.com/my-awesome-repo/awesome-card/master/awesome-card.js",
      "visit_repo": "https://github.com/my-awesome-repo/awesome-card",
      "changelog": "https://github.com/my-awesome-repo/awesome-card/releases/latest"
    }
}
```

### Example instructions for your readme

```text
### Installation and tracking with `custom_updater`

1. Make sure that you have [`custom_updater`](https://github.com/custom-components/custom_updater) installed, configured and in a working state.
2. Configure Lovelace to load the card.

resources:
  - url: /customcards/github/my-awesome-repo/awesome-card.js?track=true
    type: module

3. Run the service `custom_updater.check_all` or click the "CHECK" button if you use the [tracker-card](https://github.com/custom-cards/tracker-card).
4. Refresh the website.
```

## More details

When the `custom_updater` see that the "url" folow the expected structure it assumes that this is compliant for the "super_custom" concept.

The expected structure is:

```text
url: /customcards/github/github-username-of-developer/custom-card-name.js?track=true
```

What the `custom_updater` does now is the check that the assumption was true.
From the example above it will try to get the data from:

```text
https://raw.githubusercontent.com/github-username-of-developer/custom-card-name/master/custom_card.json
```

```text
https://raw.githubusercontent.com/github-username-of-developer/custom-card-name/master/tracker.json
```

```text
https://raw.githubusercontent.com/github-username-of-developer/custom-card-name/master/updater.json
```

```text
https://raw.githubusercontent.com/github-username-of-developer/custom-card-name/master/custom_updater.json
```

If if get data returned from this it will continue the logic.
The next step is to verify that the json data **only** contain data about **one** card.

The next thing it does is to create directories (recursively) if they do not exist, starting with `www`/`github`.

When all that is taken care of, it will start to download the card file(s).
It will try to get these:

- custom-card-name.js
- custom-card-name.lib.js
- custom-card-name-editor.js

#### Side notes!

- If you added a card with this method, and the `www` dir did not exist, it will create it, restart og Home Assistant is **not** needed.
- This also works for all cards in  ["The master list on the GH org for custom_cards"](https://github.com/custom-cards/information/blob/master/repos.json) and those you have added with the `card_urls` option.
- Adding `?track=true` at the end of a url that does not use this concept will not do anything.