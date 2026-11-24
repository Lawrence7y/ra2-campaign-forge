// W122c: find while(ptr != 0) loops whose pointer is initialized from a .data global.
// @category W122
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.util.*;
import java.util.regex.*;

public class FindListWalks extends GhidraScript {
    public void run() throws Exception {
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        FunctionManager fm = currentProgram.getFunctionManager();
        // biggest functions first
        List<Function> fs = new ArrayList<>();
        for (Function f : fm.getFunctions(true)) fs.add(f);
        fs.sort((a,b) -> Long.compare(b.getBody().getNumAddresses(), a.getBody().getNumAddresses()));
        Pattern ploop = Pattern.compile("while\\s*\\(\\s*(\\w+)\\s*!=\\s*\\(?(?:\\w+\\s*\\*+)?\\)?\\s*0x0\\s*\\)");
        StringBuilder out = new StringBuilder();
        int done = 0, hits = 0;
        for (Function f : fs) {
            if (done >= 250) break;
            if (f.getBody().getNumAddresses() < 300) continue;
            done++;
            DecompileResults r = di.decompileFunction(f, 45, monitor);
            if (r == null || !r.decompileCompleted()) continue;
            String c = r.getDecompiledFunction().getC();
            Matcher m = ploop.matcher(c);
            while (m.find()) {
                String var = m.group(1);
                // find the assignment that seeds this variable from a DAT_ global
                Pattern pa = Pattern.compile("\\b" + var + "\\s*=\\s*[^;]*?(DAT_[0-9a-fA-F]+|[A-Za-z_]+_00[0-9a-fA-F]+)[^;]*;");
                Matcher ma = pa.matcher(c);
                String seed = null;
                while (ma.find()) { seed = ma.group(1); break; }
                if (seed != null) {
                    hits++;
                    out.append(f.getEntryPoint()).append("  size=").append(f.getBody().getNumAddresses())
                       .append("  var=").append(var).append("  seed=").append(seed)
                       .append("  line=").append(m.group(0).trim()).append("\n");
                    break;
                }
            }
        }
        println("W122c decompiled=" + done + " listwalk-seeded-from-global=" + hits);
        println(out.toString());
    }
}