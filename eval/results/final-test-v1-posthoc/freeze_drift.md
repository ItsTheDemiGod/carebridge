# POST-HOC: templates.json freeze-drift proof

Compared with tag `freeze-pre-test`: strings 698 -> 800.
- added keys: 102 (all under ui.*: True)
- removed keys: 0
- changed keys: 2: ui.testing.method.test, ui.testing.limits.l2
- other top-level fields changed: none
- changed or removed outside ui.*: none

Freeze manifest verify (`backend/.venv/Scripts/python scripts/freeze_manifest.py verify`, 98 hashed files plus hash-only items), exact output:

```
DRIFT:
changed: data/templates/templates.json
```

No other file covered by the manifest differs from its frozen hash. The runtime was not affected: the 102 added ui.* keys are front-end page strings (testing page, written after the run); the two changed strings are the testing-page sentences that said the final test "has not been run yet".
