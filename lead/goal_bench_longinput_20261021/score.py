"""长输入可靠性基准评分器。

输入：各模型交付的 answers/<model>.json（或从原始文本里解析）
评分：canary 召回、精确计数、尾部标记、格式合规
"""
import json
import re
import sys
from pathlib import Path

OUT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal_bench_longinput_20261021")
ANS = OUT / "answers"


def load_truth(tier):
    name = "ground_truth_60k.json" if tier == "60k" else "ground_truth.json"
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def extract_json(text):
    """从模型回复里抠出第一个平衡的 JSON 对象。"""
    if not text:
        return None
    # 去 ```json 围栏
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    cand = m.group(1) if m else None
    if cand is None:
        start = text.find("{")
        if start < 0:
            return None
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    cand = text[start:i + 1]
                    break
    if cand is None:
        return None
    try:
        return json.loads(cand)
    except Exception:
        return None


def score_one(tier, model, raw_text, truth):
    """返回评分字典。raw_text 为模型原始输出文本。"""
    obj = extract_json(raw_text)
    res = {
        "model": model, "tier": tier,
        "delivered": bool(raw_text and raw_text.strip()),
        "json_parse_ok": obj is not None,
        "raw_len": len(raw_text or ""),
    }
    if obj is None:
        res.update({"verdict": "NO_JSON", "score": 0.0})
        return res

    canaries = truth["canaries"]
    got = obj.get("canaries") or {}
    if not isinstance(got, dict):
        got = {}
    hit = 0
    detail = {}
    for cid, want in canaries.items():
        have = str(got.get(cid, "")).strip()
        ok = have == want
        detail[cid] = {"want": want, "got": have, "ok": ok}
        hit += ok
    res["canary_hit"] = hit
    res["canary_total"] = len(canaries)
    res["canary_detail"] = detail

    # 精确计数
    def as_int(v):
        try:
            return int(str(v).strip())
        except Exception:
            return None

    cnt_ok = 0
    cnt_detail = {}
    for key in ("count_0x0084F2BA", "count_eof_marker"):
        want = truth[key]
        have = as_int(obj.get(key))
        ok = have == want
        cnt_detail[key] = {"want": want, "got": have, "ok": ok}
        cnt_ok += ok
    res["count_hit"] = cnt_ok
    res["count_detail"] = cnt_detail

    # 尾部标记
    tail_ok = str(obj.get("tail_marker", "")).strip() == truth["tail_marker_expected"]
    res["tail_ok"] = tail_ok

    # 综合分：canary 召回 70% + 计数 20% + 尾部 10%
    score = (hit / len(canaries)) * 0.7 + (cnt_ok / 2) * 0.2 + (0.1 if tail_ok else 0.0)
    res["score"] = round(score, 4)
    if hit == len(canaries) and cnt_ok == 2 and tail_ok:
        res["verdict"] = "PERFECT"
    elif hit >= len(canaries) * 0.9:
        res["verdict"] = "GOOD"
    elif hit >= len(canaries) * 0.5:
        res["verdict"] = "PARTIAL"
    else:
        res["verdict"] = "POOR"
    return res


def main():
    tier = sys.argv[1] if len(sys.argv) > 1 else "60k"
    truth = load_truth(tier)
    if "tail_marker_expected" not in truth:
        # 从 tail120 里抠出 marker
        m = re.search(r"EOF-MARKER-[0-9A-F]{4}", truth.get("tail120", ""))
        truth["tail_marker_expected"] = m.group(0) if m else ""
    results = []
    for p in sorted(ANS.glob(f"*_{tier}.txt")):
        model = p.name[: -len(f"_{tier}.txt")]
        raw = p.read_text(encoding="utf-8", errors="replace")
        results.append(score_one(tier, model, raw, truth))

    print(f"=== tier {tier} | truth bytes={truth['corpus_bytes']:,} ===")
    print(f"{'model':34} {'deliv':>6} {'json':>5} {'canary':>8} {'cnt':>4} {'tail':>5} {'score':>7}  verdict")
    for r in results:
        print(f"{r['model']:34} {str(r['delivered']):>6} {str(r['json_parse_ok']):>5} "
              f"{str(r.get('canary_hit','-'))+'/'+str(r.get('canary_total','-')):>8} "
              f"{str(r.get('count_hit','-'))+'/2':>4} "
              f"{str(r.get('tail_ok','-')):>5} {r['score']:>7}  {r['verdict']}")

    (OUT / f"score_{tier}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT / f'score_{tier}.json'}")


if __name__ == "__main__":
    main()
