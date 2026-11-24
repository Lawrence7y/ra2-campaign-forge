// W131: FIELD LAYOUT extraction -- for each (class, method) decompile and tally
// the `this`-relative offsets actually touched. Milestone (4): "关键结构条目".
// @category W131
//
// Input file lines: <classname>\t<hex entry>
// Output lines  : <classname>\t<offset hex>\t<R|W>\t<count>\t<width hint>
//
// Method: in __thiscall methods Ghidra names the object param_1. The decompiled C
// expresses field access as either
//     *(undefined4 *)(param_1 + 0x54)
//     param_1->field_0x54
// so a line-level regex is enough. A line that assigns to such an expression is a
// write; otherwise it is a read. Width is taken from the cast type.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.util.*;
import java.util.regex.*;

public class FieldLayout extends GhidraScript {
    static final Pattern P_PAREN = Pattern.compile(
            "\\*\\((\\w+) \\*\\)\\((\\w+) \\+ (0x[0-9a-f]+)\\)");
    static final Pattern P_ARROW = Pattern.compile("(\\w+)->field_(0x[0-9a-f]+)");
    // alias discovery: `iVar1 = param_1;` or `iVar1 = (int)param_1;`
    static final Pattern P_ALIAS = Pattern.compile(
            "^\\s*(\\w+) = \\(?[\\w ]*\\)?param_1;\\s*$");

    /** Collect local aliases of param_1 so `iVar1 + 0x54` is still counted. */
    Set<String> aliases(String[] lines) {
        Set<String> a = new HashSet<>();
        a.add("param_1");
        for (String s : lines) {
            Matcher m = P_ALIAS.matcher(s);
            if (m.find()) a.add(m.group(1));
        }
        // also treat `x = param_1->field_...` no; keep it simple and conservative
        return a;
    }

    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) { println("usage: FieldLayout.java <classfn.txt>"); return; }
        FunctionManager fm = currentProgram.getFunctionManager();
        AddressSpace as = currentProgram.getAddressFactory().getDefaultAddressSpace();
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        // class -> offset -> [reads, writes, widthHist]
        Map<String, Map<Long, int[]>> agg = new LinkedHashMap<>();
        Map<String, String> widthOf = new HashMap<>();
        BufferedReader br = new BufferedReader(new FileReader(new File(args[0])));
        String line;
        int done = 0, failed = 0;
        while ((line = br.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            String[] p = line.split("\t");
            if (p.length < 2) continue;
            String cls = p[0];
            long va;
            try { va = Long.parseLong(p[1].replace("0x", ""), 16); } catch (Exception e) { continue; }
            Function f = fm.getFunctionAt(as.getAddress(va));
            if (f == null) f = fm.getFunctionContaining(as.getAddress(va));
            if (f == null) { failed++; continue; }
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            if (r == null || !r.decompileCompleted()) { failed++; continue; }
            String[] ls = r.getDecompiledFunction().getC().split("\n");
            Set<String> alias = aliases(ls);
            Map<Long, int[]> m = agg.computeIfAbsent(cls, k -> new TreeMap<>());
            for (String s : ls) {
                Matcher mp = P_PAREN.matcher(s);
                while (mp.find()) {
                    String ty = mp.group(1);
                    String base = mp.group(2);
                    if (!alias.contains(base)) continue;
                    long off = Long.parseLong(mp.group(3).replace("0x", ""), 16);
                    int[] c = m.computeIfAbsent(off, k -> new int[2]);
                    boolean isWrite = isWriteLine(s, mp.group(3));
                    if (isWrite) c[1]++; else c[0]++;
                    widthOf.putIfAbsent(cls + ":" + off, ty);
                }
                Matcher ma = P_ARROW.matcher(s);
                while (ma.find()) {
                    if (!alias.contains(ma.group(1))) continue;
                    long off = Long.parseLong(ma.group(2).replace("0x", ""), 16);
                    int[] c = m.computeIfAbsent(off, k -> new int[2]);
                    boolean isWrite = isWriteLine(s, "0x" + ma.group(2).replace("0x", ""));
                    if (isWrite) c[1]++; else c[0]++;
                }
            }
            done++;
            if ((done % 100) == 0) println("### progress " + done);
        }
        br.close();
        println("### decompiled=" + done + " failed=" + failed);
        println("class\toffset\treads\twrites\twidth");
        for (Map.Entry<String, Map<Long, int[]>> e : agg.entrySet()) {
            for (Map.Entry<Long, int[]> o : e.getValue().entrySet()) {
                String w = widthOf.getOrDefault(e.getKey() + ":" + o.getKey(), "?");
                println(String.format("%s\t0x%x\t%d\t%d\t%s", e.getKey(),
                        o.getKey(), o.getValue()[0], o.getValue()[1], w));
            }
        }
        println("### DONE");
    }

    /** True when this occurrence of the offset sits on the left of an assignment. */
    boolean isWriteLine(String line, String offLiteral) {
        int idx = line.indexOf(offLiteral);
        if (idx < 0) return false;
        int eq = line.indexOf('=');
        // exclude ==, <=, >=, !=
        while (eq >= 0) {
            char prev = eq > 0 ? line.charAt(eq - 1) : ' ';
            char next = eq + 1 < line.length() ? line.charAt(eq + 1) : ' ';
            if (prev != '=' && prev != '<' && prev != '>' && prev != '!' && next != '=') break;
            eq = line.indexOf('=', eq + 1);
        }
        return eq > idx;
    }
}
