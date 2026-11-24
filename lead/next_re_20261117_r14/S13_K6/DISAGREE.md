# S13-K6 DISAGREE

## D1 · 49 vs 45
Binary scan found 49 DynamicVectorClass rows with uniform slot contracts; card asked for 45. I delivered exactly 45 and explicitly listed the 4 omitted rows in UNKNOWNS. No false row was added to reach a round number.
## D2 · ring4 strength is not uniform
For slot2/4 with a global-array anchor, ring4 is an exact same-vtable virtual dispatch in a graded caller. For slot0/1/3/5 it is a graded external slot-dispatch baseline. If audit requires per-object dataflow for every virtual call, those rows should be challenged; I am not claiming more than the evidence shows.
## D3 · inherited method naming
slot1 and slot5 are inherited VectorClass methods exposed through DynamicVectorClass vtables. Names use VectorClass<T>::... rather than DynamicVectorClass<T>::...; RTTI still proves the concrete container element type. Prior truncated names are placeholders, not different semantics.
## D4 · container-template denominator
S13-K5 D1 is unresolved. This card changes grade in place for S13 rows; it does not decide whether the 240 denominator should exclude container templates.
