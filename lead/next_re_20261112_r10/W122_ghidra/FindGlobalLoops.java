// W122: find loops whose condition reads a GLOBAL, by decompiling functions
// that contain a large back-jump loop. Prints function entry + the loop line.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.util.*;

public class FindGlobalLoops extends GhidraScript {
    public void run() throws Exception {
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        int done = 0, hits = 0;
        StringBuilder sb = new StringBuilder();
        for (Function f : fm.getFunctions(true)) {
            if (done >= 400) break;
            Listing lst = currentProgram.getListing();
            // cheap prefilter: function must contain a "while"/"for" after decompile;
            // we just decompile the biggest 400 functions
            if (f.getBody().getNumAddresses() < 200) continue;
            done++;
            DecompileResults res = di.decompileFunction(f, 30, monitor);
            if (res == null || !res.decompileCompleted()) continue;
            String c = res.getDecompiledFunction().getC();
            String[] lines = c.split("\n");
            for (String ln : lines) {
                String t = ln.trim();
                if ((t.startsWith("while (") || t.startsWith("for (") || t.startsWith("do {"))
                    && t.contains("0x") && (t.contains("DAT_") || t.contains("_DAT"))) {
                    hits++;
                    sb.append(String.format("%s | %s%n", f.getEntryPoint(), t));
                    break;
                }
            }
        }
        println("W122 decompiled=" + done + " loop-with-global=" + hits);
        println(sb.toString());
    }
}