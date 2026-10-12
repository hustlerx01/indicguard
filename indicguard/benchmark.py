"""python -m indicguard.benchmark [--data data/indic_pi.jsonl] -> per-language/split P/R/F1 for IndicGuard vs English baseline."""
import argparse, json, pathlib
from collections import defaultdict
from .detector import detect, english_baseline

def prf(rows):
    tp = sum(r["pred"] and r["label"] for r in rows); fp = sum(r["pred"] and not r["label"] for r in rows)
    fn = sum((not r["pred"]) and r["label"] for r in rows)
    p = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * rc / (p + rc) if p + rc else 0.0
    hard = [r for r in rows if r["hard"]]
    return {"n": len(rows), "tp": tp, "fp": fp, "fn": fn, "precision": round(p, 3), "recall": round(rc, 3), "f1": round(f, 3),
            "hard_benign_fpr": round(sum(r["pred"] for r in hard) / len(hard), 3) if hard else None}

def run(path):
    data = [json.loads(l) for l in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    out = {}
    for name, fn in [("indicguard", detect), ("english_baseline", english_baseline)]:
        rows = [dict(d, pred=fn(d["text"])["injection"]) for d in data]
        groups = defaultdict(list)
        for r in rows:
            groups["ALL"].append(r); groups[f"split={r['split']}"].append(r); groups[f"lang={r['lang']}"].append(r)
        out[name] = {k: prf(v) for k, v in sorted(groups.items())}
        out[name]["errors"] = [{"id": r["id"], "lang": r["lang"], "split": r["split"], "label": r["label"], "text": r["text"]} for r in rows if r["pred"] != bool(r["label"])]
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default=str(pathlib.Path(__file__).resolve().parent.parent / "data/indic_pi.jsonl"))
    res = run(ap.parse_args().data)
    for name in res:
        print(f"\n== {name}")
        for k, v in res[name].items():
            if k != "errors":
                print(f"{k:16} n={v['n']:3} P={v['precision']:.3f} R={v['recall']:.3f} F1={v['f1']:.3f} hardFPR={v['hard_benign_fpr']}")
        print("errors:", len(res[name]["errors"]))
    print(json.dumps(res["indicguard"]["errors"], ensure_ascii=False, indent=1))
    pathlib.Path("results").mkdir(exist_ok=True)
    pathlib.Path("results/benchmark.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
