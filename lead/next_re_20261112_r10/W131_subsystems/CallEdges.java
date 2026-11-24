// W131: dump the CALL GRAPH (caller -> callee) for all contiguous functions.
// @category W131
//
// Enables evidence layer L5: propagate a subsystem label along edges. This is a
// real signal (a function that only calls/gets called by one subsystem's code is
// likely part of it) -- unlike address adjacency, which this project forbids.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class CallEdges extends GhidraScript {
    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager rm = currentProgram.getReferenceManager();
        println("caller\tcallee\tsite");
        int edges = 0, fns = 0;
        for (Function f : fm.getFunctions(true)) {
            long from = f.getEntryPoint().getOffset();
            fns++;
            LinkedHashSet<Long> seen = new LinkedHashSet<>();
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (Reference r : ins.getReferencesFrom()) {
                    if (!r.getReferenceType().isCall()) continue;
                    Address t = r.getToAddress();
                    if (t == null) continue;
                    Function tf = fm.getFunctionAt(t);
                    if (tf == null) tf = fm.getFunctionContaining(t);
                    if (tf == null) continue;
                    long to = tf.getEntryPoint().getOffset();
                    if (to == from) continue;
                    // one edge per (site,target) but keep all call sites
                    println(String.format("%08x\t%08x\t%08x", from, to, ins.getAddress().getOffset()));
                    edges++;
                    seen.add(to);
                }
            }
        }
        println("### EDGES " + edges + " funcs=" + fns);
    }
}
