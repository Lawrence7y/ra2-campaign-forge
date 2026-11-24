// W122f: Pcode-level back-slicing. Find CBRANCH conditions that trace back to a
// LOAD from a .data global. Prints function, branch addr, and the global address.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.pcode.*;
import java.util.*;

public class PcodeSlice extends GhidraScript {
    static final long DATA_LO = 0x812000L, DATA_HI = 0xB79BE4L;
    static final int MAXDEPTH = 14;

    // returns first .data global address reached from v, or -1
    long trace(Varnode v, int depth, Set<Long> seen) {
        if (v == null || depth > MAXDEPTH) return -1;
        long key = v.getOffset();
        if (!v.isUnique() && !v.isConstant() && !seen.add(key)) return -1;
        PcodeOp def = v.getDef();
        if (def == null) return -1;
        int op = def.getOpcode();
        if (op == PcodeOp.LOAD) {
            Varnode addr = def.getInput(1);
            if (addr != null && addr.isConstant()) {
                long a = addr.getOffset();
                if (a >= DATA_LO && a < DATA_HI) return a;
            }
        }
        int n = def.getNumInputs();
        for (int i = 0; i < n; i++) {
            long r = trace(def.getInput(i), depth + 1, seen);
            if (r != -1) return r;
        }
        return -1;
    }

    public void run() throws Exception {
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        List<Function> fs = new ArrayList<>();
        for (Function f : fm.getFunctions(true)) fs.add(f);
        fs.sort((a,b) -> Long.compare(b.getBody().getNumAddresses(), a.getBody().getNumAddresses()));
        int done = 0, hits = 0;
        StringBuilder out = new StringBuilder();
        for (Function f : fs) {
            if (done >= 220) break;
            if (f.getBody().getNumAddresses() < 400) continue;
            done++;
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            if (r == null || !r.decompileCompleted()) continue;
            HighFunction hf = r.getHighFunction();
            if (hf == null) continue;
            Iterator<PcodeOpAST> it = hf.getPcodeOps();
            Map<Long,Long> found = new LinkedHashMap<>();
            while (it.hasNext()) {
                PcodeOpAST op = it.next();
                if (op.getOpcode() != PcodeOp.CBRANCH) continue;
                if (op.getNumInputs() < 2) continue;
                long g = trace(op.getInput(1), 0, new HashSet<Long>());
                if (g != -1) found.put(op.getSeqnum().getTarget().getOffset(), g);
            }
            if (!found.isEmpty()) {
                for (Map.Entry<Long,Long> e : found.entrySet()) {
                    hits++;
                    out.append(String.format("%s size=%d branch@%08x global@%08x%n",
                        f.getEntryPoint(), f.getBody().getNumAddresses(), e.getKey(), e.getValue()));
                }
            }
        }
        println("W122f decompiled=" + done + " branch-hits=" + hits);
        println(out.toString());
    }
}