"""One-time positive-only tolerance evidence; does not alter any thresholds."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.analyze_edge_quality import analyze_svg_edges, save_evidence, RULES
from tools.run_visual_e2e import run_bounded


def worker():
    folder = Path(__file__).resolve().parent
    evidence = folder / "positive-calibration"
    evidence.mkdir(exist_ok=True)
    records = []
    for fixture in sorted((folder / "fixtures").glob("*.svg")):
        for size in (128, 256):
            report, maps = analyze_svg_edges(fixture.read_text(encoding="utf-8"), size=size)
            save_evidence(evidence / (fixture.stem + "-" + str(size)), report, maps)
            records.append({"fixture": fixture.name, "size": size, "status": report["status"], "metrics": report["metrics"]})
            print(fixture.name, size, report["status"], json.dumps({k: {p:v for p,v in report['metrics'][k].items() if p in {'mae_0_255','large_error_fraction'}} for k in ('coverage','color')}), flush=True)
    data = {"phase": "positive-only fixture replay; global limits fixed before first negative run; local limit fixed from positive component counts before first short-arc injection; this script never tunes limits", "rules": RULES, "records": records}
    (evidence / "summary.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return 0 if all(record["status"] == "no_rule_failure" for record in records) else 2


if __name__ == "__main__":
    if "--worker" in sys.argv:
        raise SystemExit(worker())
    raise SystemExit(run_bounded([sys.executable, "-B", __file__, "--worker"], timeout=40))
