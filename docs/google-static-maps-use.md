# Google Static Maps Use Note

PaveBench public datasets must not use Google Maps Static API imagery, cached Google map images, or Google map tiles as benchmark inputs.

This is the conservative reading of the current Google Maps Platform terms:

- Maps Static API is listed as a Google Maps Platform Core Service.
- The Maps Static API docs say its use is subject to Google Maps Platform Terms of Service.
- The current Google Maps Platform Terms restrict exporting, extracting, storing, resharing, rehosting, or caching Google Maps Content outside the services unless expressly permitted.
- The same terms restrict creating content from Google Maps Content, including using it to train, test, validate, or fine-tune ML/AI models.
- Map Tiles API policies explicitly call out image analysis, machine interpretation, object detection/identification, and geodata extraction as disallowed non-visualization uses.

Sources:

- Google Maps Platform Core Services Summary: https://cloud.google.com/maps-platform/terms/maps-services
- Maps Static API overview: https://developers.google.com/maps/documentation/maps-static/overview
- Google Maps Platform Terms of Service: https://cloud.google.com/maps-platform/terms
- Map Tiles API Policies: https://developers.google.com/maps/documentation/tile/policies

This file is not legal advice. It is a benchmark hygiene rule: use redistributable public-domain imagery for public PaveBench releases.
