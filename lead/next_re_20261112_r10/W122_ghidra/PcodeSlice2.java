// W122g: optimized Pcode back-slicing.
//  - only BACK-EDGE branches (CBRANCH target <= branch address)  -> loop conditions only
//  - reuse a visit-stamp array instead of allocating a HashSet per branch
//  - cap to the N largest functions
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.pcode.*;
import java.util.*;

public class PcodeSlice2 extends GhidraScript {
    static final long DATA_LO = 0x812000L, DATA_HI = 0xB79BE4L;
    static final int MAXDEPTH = 12;
    HashMap<Long,Integer> seen = new HashMap<Long,Integer>();
    int stamp = 0;

    long trace(Varnode v, int depth) {
        if (v == null || depth > MAXDEPTH) return -1;
        Long key = Long.valueOf(v.getOffset());
        Integer prev = seen.get(key);
        if (prev != null && prev.intValue() == stamp) return -1;
        seen.put(key, Integer.valueOf(stamp));
        PcodeOp def = v.getDef();
        if (def == null) return -1;
        if (def.getOpcode() == PcodeOp.LOAD) {
            Varnode a = def.getInput(1);
            if (a != null && a.isConstant()) {
                long g = a.getOffset();
                if (g >= DATA_LO && g < DATA_HI) return g;
            }
        }
        int n = def.getNumInputs();
        for (int i = 0; i < n; i++) {
            long r = trace(def.getInput(i), depth + 1);
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
        int done = 0, hits = 0, branches = 0;
        StringBuilder out = new StringBuilder();
        for (Function f : fs) {
            if (done >= 60) break;
            if (f.getBody().getNumAddresses() < 500) continue;
            done++;
            DecompileResults r = di.decompileFunction(f, 45, monitor);
            if (r == null || !r.decompileCompleted()) continue;
            HighFunction hf = r.getHighFunction();
            if (hf == null) continue;
            Iterator<PcodeOpAST> it = hf.getPcodeOps();
            Set<Long> rec = new LinkedHashSet<>();
            while (it.hasNext()) {
                PcodeOpAST op = it.next();
                if (op.getOpcode() != PcodeOp.CBRANCH) continue;
                long at = op.getSeqnum().getTarget().getOffset();
                if (op.getNumInputs() < 2) continue;
                Varnode dest = op.getInput(0);
                if (dest == null || !dest.isAddress()) continue;
                long tgt = dest.getAddress().getOffset();
                if (tgt > at) continue;          // keep only back-edges
                branches++;
                stamp++;
                long g = trace(op.getInput(1), 0);
                if (g != -1) { rec.add(at | (g << 32)); hits++; }
            }
            for (long v : rec) {
                out.append(String.format("%s size=%d branch@%08x global@%08x%n",
                        f.getEntryPoint(), f.getBody().getNumAddresses(),
                        (int)(v & 0xFFFFFFFFL), (int)(v >>> 32)));
            }
        }
        println("W122g decompiled=" + done + " backedges=" + branches + " hits=" + hits);
        println(out.toString());
    }
}