You can disable tracking of _any_ custom_card by adding `?track=false` at the end of the url in your lovelace config.

Example:
```yaml
resources:
  - url: /customcards/my-custom-card.js?track=false
    type: module
```