# Publication Checklist

Before tagging a public dataset release:

- [ ] All imagery is redistributable and has source/license metadata.
- [ ] No Google Maps, Google Static Maps, Map Tiles, or cached commercial basemap imagery is present.
- [ ] Every case has `metadata.json`.
- [ ] Human-trace guide cases have been reviewed or are clearly marked `needs_gold_review`.
- [ ] Real benchmark cases are marked `reviewed_gold`.
- [ ] `python3 -m pytest` passes.
- [ ] Oracle baseline scores pass on all reviewed-gold cases.
- [ ] Leaderboard tables are split by track.
- [ ] Dataset version is tagged in GitHub.
