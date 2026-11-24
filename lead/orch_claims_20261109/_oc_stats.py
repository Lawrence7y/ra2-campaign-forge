# -*- coding: utf-8 -*-
"""_oc_stats.py : deterministic classification and distribution of the 20 claims.

NOTE: several claim strings are self-deprecating *paraphrases* in this task's
CLAIMS list; the literal archived task books sometimes say something weaker
(a question, a hedged hypothesis, or no such assertion at all). Those are
marked below with `literal_in_taskbook`.
"""
import json

# id, verdict, primary_nature, all_natures, caught_by_subtask, misdirected_downstream,
# literal_in_taskbook ("yes" | "hedged" | "no" | "self_recount" | "only_in_this_task")
C = [
 (1,  "wrong_numeric",     "数少", ["数少"],                     True,  True,  "yes"),
 (2,  "wrong_numeric",     "数少", ["数少","口径混淆"],           True,  True,  "yes"),
 (3,  "wrong_convention",  "口径混淆", ["口径混淆"],              True,  True,  "yes"),
 (4,  "wrong_numeric",     "数多", ["数多","口径混淆"],           True,  True,  "yes"),
 (5,  "wrong_convention",  "口径混淆", ["口径混淆"],              True,  True,  "yes"),
 (6,  "wrong_object",      "把设计实验当实跑", ["把设计实验当实跑","串对象"], True, True, "hedged"),
 (7,  "wrong_object",      "串对象", ["串对象"],                  True,  True,  "hedged"),
 (8,  "wrong_numeric",     "数多", ["数多","串对象"],             True,  True,  "yes"),
 (9,  "imprecise",         "口径混淆", ["口径混淆"],              True,  True,  "yes"),
 (10, "wrong_object",      "串对象", ["串对象","口径混淆"],        True,  True,  "hedged"),
 (11, "wrong_object",      "串对象", ["串对象"],                  True,  True,  "no"),
 (12, "wrong_numeric",     "数少", ["数少"],                     True,  True,  "yes"),
 (13, "wrong_object",      "口径混淆", ["口径混淆"],              True,  True,  "yes"),
 (14, "wrong_numeric",     "数多", ["数多"],                     True,  True,  "hedged"),
 (15, "wrong_convention",  "口径混淆", ["口径混淆"],              True,  True,  "no"),
 (16, "wrong_object",      "串对象", ["串对象"],                  True,  True,  "hedged"),
 (17, "wrong_object",      "口径混淆", ["口径混淆"],              True,  True,  "no"),
 (18, "wrong_convention",  "口径混淆", ["口径混淆"],              True,  True,  "hedged"),
 (19, "wrong_numeric",     "代数错", ["代数错"],                  False, False, "self_recount"),
 (20, "wrong_numeric",     "代数错", ["代数错"],                  False, False, "self_recount"),
]

N = len(C)
n_wrong = sum(1 for c in C if c[1] not in ("correct", "imprecise"))
n_imprecise = sum(1 for c in C if c[1] == "imprecise")
n_correct = sum(1 for c in C if c[1] == "correct")
n_caught = sum(1 for c in C if c[4])
n_notcaught = N - n_caught
n_misdirect = sum(1 for c in C if c[5])
n_literal = sum(1 for c in C if c[6] == "yes")
n_hedged = sum(1 for c in C if c[6] == "hedged")
n_no_literal = sum(1 for c in C if c[6] == "no")
n_self = sum(1 for c in C if c[6] == "self_recount")

primary = {}
alln = {}
verd = {}
for c in C:
    primary[c[2]] = primary.get(c[2], 0) + 1
    verd[c[1]] = verd.get(c[1], 0) + 1
    for x in c[3]:
        alln[x] = alln.get(x, 0) + 1

out = {
  "total": N,
  "wrong": n_wrong, "imprecise": n_imprecise, "correct": n_correct,
  "accuracy_strict": n_correct / N,
  "accuracy_with_imprecise": (n_correct + n_imprecise) / N,
  "verdict_distribution": verd,
  "primary_nature_distribution": primary,
  "all_natures_distribution_non_exclusive": alln,
  "most_common_primary": max(primary.items(), key=lambda kv: kv[1]),
  "caught_by_subtask": n_caught,
  "not_caught": n_notcaught,
  "not_caught_ids": [c[0] for c in C if not c[4]],
  "misdirected_downstream": n_misdirect,
  "literal_in_taskbook": {"yes": n_literal, "hedged_or_question": n_hedged,
                          "no_such_assertion": n_no_literal,
                          "self_recount_only": n_self},
  "numeric_undercount_ids": [1, 2, 12],
  "numeric_overcount_ids": [4, 8, 14],
  "algebra_ids": [19, 20],
}
print(json.dumps(out, ensure_ascii=False, indent=2))
