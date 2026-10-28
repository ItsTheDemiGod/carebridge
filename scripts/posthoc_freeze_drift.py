"""POST-HOC: prove templates.json differs from tag freeze-pre-test only in ui.* keys. Read-only."""
import json, subprocess, sys
old = json.loads(subprocess.check_output(["git", "show", "freeze-pre-test:data/templates/templates.json"]).decode("utf-8"))
new = json.load(open("data/templates/templates.json", encoding="utf-8"))
o, n = old["strings"], new["strings"]
added = [k for k in n if k not in o]
removed = [k for k in o if k not in n]
changed = [k for k in o if k in n and o[k] != n[k]]
other = [k for k in old if k != "strings" and old[k] != new[k]] + [k for k in new if k not in old]
bad = [k for k in added + removed + changed if not k.startswith("ui.")] + other
out = ["# POST-HOC: templates.json freeze-drift proof", "",
       f"Compared with tag `freeze-pre-test`: strings {len(o)} -> {len(n)}.",
       f"- added keys: {len(added)} (all under ui.*: {all(k.startswith('ui.') for k in added)})",
       f"- removed keys: {len(removed)}",
       f"- changed keys: {len(changed)}: {', '.join(changed)}",
       f"- other top-level fields changed: {other or 'none'}",
       f"- changed or removed outside ui.*: {bad or 'none'}"]
open("eval/results/final-test-v1-posthoc/freeze_drift.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out)); sys.exit(1 if bad else 0)
