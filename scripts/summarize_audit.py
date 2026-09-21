import json

try:
    with open("audit_results.json", encoding="utf-16") as f:
        data = json.load(f)
except Exception:
    with open("audit_results.json", encoding="utf-8") as f:
        data = json.load(f)

print(f"Total modules scanned: {len(data)}")
synth = [d for d in data if d.get("synthetic_violations")]
print(f"\nModules with synthetic violations ({len(synth)}):")
for d in synth:
    issues = [v["issue"] for v in d["synthetic_violations"]]
    print(f"  - {d['file']}: {len(d['synthetic_violations'])} violations: {issues}")
    for v in d["synthetic_violations"]:
        print(f"      Line {v['line']}: {v['text']}")

verdicts = {}
for d in data:
    v = d.get("verdict", "UNKNOWN")
    verdicts[v] = verdicts.get(v, 0) + 1
print("\nVerdicts distribution:", verdicts)

make_real = [d for d in data if d.get("verdict") == "MAKE_REAL"]
print(f"\nMAKE_REAL modules ({len(make_real)}):")
for m in make_real:
    print(f"  - {m['file']} (Score: {m['scores']['overall']}%, Authenticity: {m['scores']['authenticity']}%)")

completeness_issues = [d for d in data if d.get("scores", {}).get("completeness", 100) < 100]
print(f"\nCompleteness issues ({len(completeness_issues)}):")
for d in completeness_issues:
    print(f"  - {d['file']} (Completeness: {d['scores']['completeness']}%)")
    if d.get("not_implemented"):
        print(f"      not_implemented lines: {d['not_implemented']}")
    if d.get("pass_only_functions"):
        print(f"      pass_only_functions: {d['pass_only_functions']}")
    if d.get("bare_excepts"):
        print(f"      bare_excepts lines: {d['bare_excepts']}")
