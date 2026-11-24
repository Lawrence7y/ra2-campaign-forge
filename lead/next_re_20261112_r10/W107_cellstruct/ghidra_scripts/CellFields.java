import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.lang.Register;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.listing.Parameter;
import ghidra.program.model.scalar.Scalar;

import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * W107 CellClass field layout scanner.
 * Pass1: disassembly scan of all [reg+disp] accesses (disp < 0x400), find functions
 *        touching disp 0xE4 (cell chain A head) and stride 0x148 sites.
 * Pass2: decompile those functions + anchors; track parameter provenance via alias graph
 *        so that only accesses through the CELL pointer are kept (chain objects, loaded
 *        values, other classes are separated).
 * Pass3: merged offset table + stride evidence.
 */
public class CellFields extends GhidraScript {

    static final String OUT =
        "D:\\Project\\ra2-campaign-forge\\lead\\next_re_20261112_r10\\W107_cellstruct\\EVIDENCE\\";

    static final long[] ANCHORS = {
        0x0047EA90L, 0x0047C520L, 0x0047C4D0L, 0x00429DC0L, 0x00429E54L, 0x00429E5FL, 0x004358A9L
    };

    static final int LIMIT = 600;

    // *(cast *)(base + disp)   or  *(cast *)base
    static final Pattern P_ACC1 = Pattern.compile(
        "\\*\\s*\\(\\s*((?:const\\s+)?[A-Za-z_][\\w\\s]*?\\*{1,2})\\s*\\)\\s*\\(?\\s*([A-Za-z_]\\w*)\\s*" +
        "(?:\\+\\s*(0x[0-9a-fA-F]+|\\d+))?\\s*\\)?");
    // *base        (no cast, disp 0)
    static final Pattern P_ACC2 = Pattern.compile("\\*\\s*([A-Za-z_]\\w*)\\b");
    // *(base + disp)  (no cast)
    static final Pattern P_ACC3 = Pattern.compile(
        "\\*\\s*\\(\\s*([A-Za-z_]\\w*)\\s*\\+\\s*(0x[0-9a-fA-F]+|\\d+)\\s*\\)");
    // (*var + disp)   vtable-style: offset from the value pointed by var
    static final Pattern P_ACC4 = Pattern.compile(
        "\\(\\s*\\*\\s*([A-Za-z_]\\w*)\\s*\\+\\s*(0x[0-9a-fA-F]+|\\d+)\\s*\\)");
    // var[idx]        pointer indexing, scale 4 (int*/undefined4*)
    static final Pattern P_ACCIDX = Pattern.compile(
        "\\b([A-Za-z_]\\w*)\\s*\\[\\s*(0x[0-9a-fA-F]+|\\d+)\\s*\\]");
    static final Pattern P_ASSIGN = Pattern.compile("([A-Za-z_]\\w*)\\s*=(?![=])\\s*([^;\\n]+)");
    static final Pattern P_CASTSTRIP = Pattern.compile("^\\s*\\(\\s*[\\w\\s]+\\*{1,2}\\s*\\)\\s*");
    static final Pattern P_VARARITH = Pattern.compile("^\\s*&?\\s*([A-Za-z_]\\w*)\\s*((?:[+\\-*/]\\s*[\\w\\sx]+)*)$");

    static class Acc {
        long addr; String text; String reg; long disp; String sz; String fn;
    }

    static class DAcc { // decompiled access
        String base; long disp; String cast; String line;
    }

    PrintWriter log;

    void out(String s) { log.println(s); println(s); }

    PrintWriter openFile(String name) throws Exception {
        return new PrintWriter(new OutputStreamWriter(new FileOutputStream(OUT + name), StandardCharsets.UTF_8));
    }

    static int castSize(String cast) {
        String c = cast.toLowerCase();
        if (c.contains("idx4") || c.contains("vtbl")) return 4;
        if (c.contains("double") || c.contains("undefined8") || c.contains("long long")) return 8;
        if (c.contains("float")) return 4;
        if (c.contains("undefined2") || c.contains("short")) return 2;
        if (c.contains("undefined4") || c.contains("int") || c.contains("code") || c.contains("bool")) return 4;
        if (c.contains("undefined") || c.contains("char") || c.contains("byte")) return 1;
        if (c.contains("long") || c.contains("uint")) return 4;
        return -1;
    }

    @Override
    public void run() throws Exception {
        log = openFile("run_all.log");
        long t0 = System.currentTimeMillis();

        // ---------------- PASS 1: disassembly scan ----------------
        Map<Long, List<Acc>> byFunc = new TreeMap<>();
        Map<Long, String> fnName = new TreeMap<>();
        TreeSet<Long> strideSites = new TreeSet<>();
        Set<Long> e4Funcs = new TreeSet<>();
        Listing listing = currentProgram.getListing();
        InstructionIterator it = listing.getInstructions(true);
        Function cur = null;
        int nInstr = 0, nHits = 0;
        while (it.hasNext()) {
            Instruction ins = it.next();
            nInstr++;
            Address a = ins.getAddress();
            if (cur == null || !cur.getBody().contains(a)) {
                cur = getFunctionContaining(a);
                if (cur != null) fnName.put(cur.getEntryPoint().getOffset(), cur.getName());
            }
            long fe = cur != null ? cur.getEntryPoint().getOffset() : -1;
            // stride 0x148 sites
            boolean stride = false;
            for (int i = 0; i < ins.getNumOperands(); i++)
                for (Object o : ins.getOpObjects(i))
                    if (o instanceof Scalar && ((Scalar) o).getValue() == 0x148L) stride = true;
            if (stride) strideSites.add(a.getOffset());
            // [reg + disp] accesses
            for (int i = 0; i < ins.getNumOperands(); i++) {
                Object[] objs = ins.getOpObjects(i);
                Register base = null; int nreg = 0; List<Long> sc = new ArrayList<>();
                for (Object o : objs) {
                    if (o instanceof Register) { nreg++; if (base == null) base = (Register) o; }
                    else if (o instanceof Scalar) sc.add(((Scalar) o).getValue());
                }
                if (nreg != 1 || base == null) continue;
                String bn = base.getName().toLowerCase();
                if (bn.equals("esp") || bn.equals("ebp")) continue;
                long disp = 0; boolean ok = true;
                for (long v : sc) { if (v < 0 || v >= 0x400L) { ok = false; break; } disp += v; }
                if (!ok) continue;
                Acc acc = new Acc();
                acc.addr = a.getOffset();
                acc.text = ins.toString();
                acc.reg = bn;
                acc.disp = disp;
                Matcher msz = Pattern.compile("([a-z]+)\\s+ptr").matcher(acc.text);
                acc.sz = msz.find() ? msz.group(1) : "?";
                acc.fn = cur != null ? cur.getName() : "?";
                if (fe < 0) fe = -1L;
                if (fe >= 0) byFunc.computeIfAbsent(fe, k -> new ArrayList<>()).add(acc);
                nHits++;
                if (disp == 0xE4L) e4Funcs.add(fe);
            }
        }
        out("[pass1] instructions=" + nInstr + " accesses=" + nHits + " funcs-touched=" + byFunc.size()
            + " e4funcs=" + e4Funcs.size() + " stride0x148sites=" + strideSites.size()
            + " (" + (System.currentTimeMillis() - t0) + " ms)");

        // dump all accesses (VA-level evidence)
        PrintWriter pwDump = openFile("access_dump.tsv");
        pwDump.println("funcVA\tfuncName\tinstrVA\tbase\tdisp\tsz\ttext");
        for (Map.Entry<Long, List<Acc>> e : byFunc.entrySet()) {
            for (Acc a : e.getValue())
                pwDump.println(Long.toHexString(e.getKey()) + "\t" + a.fn + "\t" + Long.toHexString(a.addr)
                    + "\t" + a.reg + "\t0x" + Long.toHexString(a.disp) + "\t" + a.sz + "\t" + a.text);
        }
        pwDump.close();

        if (getScriptArgs().length > 0 && getScriptArgs()[0].equals("pass1only")) {
            out("[done pass1only] access_dump.tsv written");
            log.close();
            return;
        }


        // ---------------- PASS 2: decompile candidates with provenance ----------------
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);

        List<Long> todo = new ArrayList<>(e4Funcs);
        for (long a : ANCHORS) {
            Function f = getFunctionContaining(toAddr(a));
            if (f != null && !todo.contains(f.getEntryPoint().getOffset()))
                todo.add(f.getEntryPoint().getOffset());
        }
        if (todo.size() > LIMIT) {
            out("[pass2] WARNING: candidate cap " + LIMIT + " of " + todo.size());
            todo = todo.subList(0, LIMIT);
        }

        // merged structures
        // disp -> (widthSet, castSet, funcSet, groupSet, examples)
        Map<Long, Set<String>> mWidth = new TreeMap<>();
        Map<Long, Set<String>> mCast = new TreeMap<>();
        Map<Long, Set<Long>> mFunc = new TreeMap<>();
        Map<Long, Set<String>> mGroup = new TreeMap<>();
        Map<Long, List<String>> mEx = new HashMap<>();
        List<String> groupC = new ArrayList<>();
        List<String> amb = new ArrayList<>();
        long maxEnd = 0; String maxEndWhere = "";

        PrintWriter pwDec = openFile("decomp_all.c");
        int ndec = 0;
        for (long fe : todo) {
            Function f = getFunctionContaining(toAddr(fe));
            if (f == null) continue;
            DecompileResults r = di.decompileFunction(f, 30, monitor);
            ndec++;
            if (r == null || !r.decompileCompleted()) {
                out("[pass2] decompile FAILED " + Long.toHexString(fe));
                continue;
            }
            String c = r.getDecompiledFunction().getC();
            pwDec.println("// ===== " + f.getName() + " @ 0x" + Long.toHexString(fe) + " =====");
            pwDec.println(c);
            pwDec.println();

            // seeds -- from the decompiled signature line itself (robust), plus API params
            Map<String, String> tag = new HashMap<>();
            int brace = c.indexOf('{');
            String header = brace > 0 ? c.substring(0, brace) : c.substring(0, Math.min(200, c.length()));
            Matcher hp = Pattern.compile("\\(([^()]*)\\)").matcher(header);
            String plist = null;
            while (hp.find()) plist = hp.group(1);
            int pn = 0;
            if (plist != null && !plist.trim().isEmpty()) {
                for (String part : plist.split(",")) {
                    String[] tk = part.trim().split("\\s+");
                    if (tk.length == 0) continue;
                    String nm = tk[tk.length - 1].replaceAll("^[*]+", "").replaceAll("\\[.*\\]", "");
                    if (!nm.matches("[A-Za-z_]\\w*") || nm.equals("void")) continue;
                    pn++;
                    tag.put(nm, "P" + pn);
                }
            }
            Parameter[] ps = f.getParameters();
            for (int i = 0; i < ps.length; i++) tag.put(ps[i].getName(), "P" + (i + 1));
            tag.put("this", "P1");
            tag.put("in_ECX", "P1"); tag.put("unaff_ECX", "P1");
            tag.put("in_ESI", "P1"); tag.put("unaff_ESI", "P1");
            tag.put("in_EDX", "P1"); tag.put("unaff_EDX", "P1");
            tag.put("in_EAX", "P1"); tag.put("unaff_EAX", "P1");

            // alias pass
            for (String chunk : c.split("[;{}]")) {
                Matcher m = P_ASSIGN.matcher(chunk);
                while (m.find()) {
                    String lhs = m.group(1), rhs = m.group(2).trim();
                    Matcher cs = P_CASTSTRIP.matcher(rhs);
                    if (cs.find()) rhs = rhs.substring(cs.end()).trim();
                    String t = null;
                    Matcher v = P_VARARITH.matcher(rhs);
                    if (v.find() && tag.containsKey(v.group(1))) t = tag.get(v.group(1));
                    if (t == null && tag.containsKey(rhs)) t = tag.get(rhs);
                    if (t == null) {
                        // deref? first access pattern in rhs
                        Matcher a1 = P_ACC1.matcher(rhs);
                        String b = null; long d = -1; String baseTag = null;
                        if (a1.find()) { b = a1.group(2); d = a1.group(3) != null ? parse(a1.group(3)) : 0; }
                        Matcher a3 = P_ACC3.matcher(rhs);
                        if (b == null && a3.find()) { b = a3.group(1); d = parse(a3.group(2)); }
                        Matcher a4 = P_ACC4.matcher(rhs);
                        if (b == null && a4.find()) { b = a4.group(1); d = parse(a4.group(2)); }
                        Matcher ax = P_ACCIDX.matcher(rhs);
                        if (b == null && ax.find()) { b = ax.group(1); d = parse(ax.group(2)) * 4L; }
                        Matcher a2 = P_ACC2.matcher(rhs);
                        if (b == null && a2.find()) { b = a2.group(1); d = 0; }
                        if (b != null) {
                            baseTag = tag.get(b);
                            if (baseTag != null && (d == 0xE4L || d == 0xE8L)) t = "OBJ_" + baseTag;
                            else if (baseTag != null && baseTag.startsWith("OBJ_")) t = baseTag;
                            else if (baseTag != null) t = "VAL_" + baseTag;
                            else t = "OTHER";
                        }
                    }
                    if (t == null) t = "OTHER";
                    tag.put(lhs, t);
                }
            }

            // access pass
            List<DAcc> daccs = new ArrayList<>();
            Set<String> blanked = new HashSet<>();
            Matcher a1 = P_ACC1.matcher(c);
            while (a1.find()) {
                DAcc d = new DAcc();
                d.cast = a1.group(1); d.base = a1.group(2);
                d.disp = a1.group(3) != null ? parse(a1.group(3)) : 0;
                d.line = a1.group(0).trim();
                daccs.add(d);
                blanked.add(a1.group(0));
            }
            String rest = c;
            for (String s : blanked) rest = rest.replace(s, "          ");
            Matcher a3 = P_ACC3.matcher(rest);
            Set<String> blank3 = new HashSet<>();
            while (a3.find()) {
                DAcc d = new DAcc();
                d.cast = "(nocast)"; d.base = a3.group(1);
                d.disp = parse(a3.group(2)); d.line = a3.group(0).trim();
                daccs.add(d);
                blank3.add(a3.group(0));
            }
            for (String s : blank3) rest = rest.replace(s, "          ");
            Matcher a4 = P_ACC4.matcher(rest);
            Set<String> blank4 = new HashSet<>();
            while (a4.find()) {
                DAcc d = new DAcc();
                d.cast = "(vtbl)"; d.base = a4.group(1);
                d.disp = parse(a4.group(2)); d.line = a4.group(0).trim();
                daccs.add(d);
                blank4.add(a4.group(0));
            }
            for (String s : blank4) rest = rest.replace(s, "          ");
            Matcher ax = P_ACCIDX.matcher(rest);
            Set<String> blankx = new HashSet<>();
            while (ax.find()) {
                DAcc d = new DAcc();
                d.cast = "(idx4)"; d.base = ax.group(1);
                d.disp = parse(ax.group(2)) * 4L; d.line = ax.group(0).trim();
                daccs.add(d);
                blankx.add(ax.group(0));
            }
            for (String s : blankx) rest = rest.replace(s, "          ");
            Matcher a2 = P_ACC2.matcher(rest);
            while (a2.find()) {
                DAcc d = new DAcc();
                d.cast = "(nocast)"; d.base = a2.group(1); d.disp = 0; d.line = a2.group(0).trim();
                daccs.add(d);
            }

            // per-tag signature
            Map<String, Set<Long>> tagDisps = new HashMap<>();
            Map<String, Set<String>> tagWidths = new HashMap<>();
            for (DAcc d : daccs) {
                String t = tag.get(d.base);
                if (t == null || d.disp >= 0x148 + 16) continue;
                if (t.startsWith("VAL_") || t.equals("OTHER")) continue;
                tagDisps.computeIfAbsent(t, k -> new TreeSet<>()).add(d.disp);
                int w = castSize(d.cast);
                tagWidths.computeIfAbsent(t, k -> new TreeSet<>())
                         .add(d.disp + ":" + (w > 0 ? w : d.cast));
            }
            List<String> sig = new ArrayList<>();
            for (Map.Entry<String, Set<Long>> e : tagDisps.entrySet()) {
                Set<Long> ds = e.getValue();
                boolean chain = ds.contains(0xE4L) || ds.contains(0xE8L);
                boolean coord = false;
                for (String w : tagWidths.getOrDefault(e.getKey(), new TreeSet<>())) {
                    String[] p = w.split(":");
                    if ((p[0].equals("36") || p[0].equals("38")) && p[1].equals("2")) coord = true;
                }
                if (chain || coord) sig.add(e.getKey() + (coord ? "+coord" : "") + (chain ? "+chain" : ""));
            }
            boolean hasChain = tagDisps.getOrDefault("P1", new TreeSet<>()).contains(0xE4L)
                || tagDisps.entrySet().stream().anyMatch(e -> e.getKey().startsWith("P") && e.getValue().contains(0xE4L));
            String group;
            Set<Long> cellDisps = null;
            String cellTag = null;
            if (!sig.isEmpty()) {
                // choose the sig tag with most disps
                String best = null; int bn2 = -1;
                for (String s : sig) {
                    String t = s.split("\\+")[0];
                    int n = tagDisps.get(t).size();
                    if (n > bn2) { bn2 = n; best = t; }
                }
                if (sig.size() > 1) amb.add(Long.toHexString(fe) + " " + f.getName() + " sig=" + sig);
                cellTag = best;
                boolean coord = false, chain = false;
                for (String s : sig) if (s.startsWith(best + "+coord")) coord = true;
                for (String s : sig) if (s.startsWith(best + "+chain")) chain = true;
                boolean shape = false;
                for (DAcc d : daccs) {
                    String t = tag.get(d.base);
                    if (t != null && t.equals("OBJ_" + best) && (d.disp == 0x2CL || d.disp == 0x30L)) shape = true;
                }
                if (coord && chain) group = "A";
                else if (chain && shape) group = "B";
                else if (coord) group = "A2";
                else group = "C";
                cellDisps = tagDisps.get(best);
            } else {
                group = "D"; // decompiled but no param-tagged field access
                cellDisps = new TreeSet<>();
            }

            // merge into global tables
            for (DAcc d : daccs) {
                if (cellTag == null) break;
                String t = tag.get(d.base);
                if (t == null || !t.equals(cellTag) || d.disp >= 0x148L) continue;
                if (!group.equals("A") && !group.equals("B") && !group.equals("A2")) continue;
                mWidth.computeIfAbsent(d.disp, k -> new TreeSet<>())
                      .add(String.valueOf(castSize(d.cast)));
                mCast.computeIfAbsent(d.disp, k -> new TreeSet<>()).add(d.cast);
                mFunc.computeIfAbsent(d.disp, k -> new TreeSet<>()).add(fe);
                mGroup.computeIfAbsent(d.disp, k -> new TreeSet<>()).add(group);
                List<String> ex = mEx.computeIfAbsent(d.disp, k -> new ArrayList<>());
                String line = "0x" + Long.toHexString(fe) + " " + f.getName() + " :: " + d.line
                    + "   [base=" + d.base + " tag=" + t + "]";
                if (!ex.contains(line) && ex.size() < 4) ex.add(line);
                int w = castSize(d.cast);
                long end = d.disp + (w > 0 ? w : 4);
                if (end > maxEnd) { maxEnd = end; maxEndWhere = Long.toHexString(fe) + " +" + Long.toHexString(d.disp); }
            }
            if (group.equals("C")) {
                Set<Long> ds = cellDisps != null ? cellDisps : new TreeSet<>();
                groupC.add("0x" + Long.toHexString(fe) + " " + f.getName()
                    + " cellTag=" + cellTag + " disps=" + ds);
            }
        }
        pwDec.close();
        out("[pass2] decompiled=" + ndec + " (" + (System.currentTimeMillis() - t0) + " ms)");

        // ---------------- PASS 3: reports ----------------
        // stride sites
        PrintWriter pw = openFile("stride_0x148_sites.txt");
        pw.println("== all instructions with scalar operand 0x148 ==");
        for (long a : strideSites) {
            Instruction ins = getInstructionAt(toAddr(a));
            Function f = getFunctionContaining(toAddr(a));
            pw.println("0x" + Long.toHexString(a) + " " + (f != null ? f.getName() : "?") + " :: " + ins);
        }
        pw.close();

        // merged table
        pw = openFile("cell_fields_merged.txt");
        pw.println("disp | widths | casts | groups | nFuncs | examples");
        for (Map.Entry<Long, Set<String>> e : mWidth.entrySet()) {
            long d = e.getKey();
            pw.println("+0x" + Long.toHexString(d)
                + " | w=" + e.getValue()
                + " | " + mCast.get(d)
                + " | " + mGroup.get(d)
                + " | n=" + mFunc.get(d).size()
                + " | " + mEx.get(d));
        }
        pw.println();
        pw.println("maxEnd=" + maxEnd + " (0x" + Long.toHexString(maxEnd) + ") at " + maxEndWhere);
        pw.println();
        pw.println("== group C (0xE4 but no coord/E8/chain-shape -> suspected other-class collision) ==");
        for (String s : groupC) pw.println(s);
        pw.println();
        pw.println("== ambiguous multi-param functions ==");
        for (String s : amb) pw.println(s);
        pw.close();

        out("");
        out("=== MERGED CELL FIELD TABLE (groups A/B/A2 only) ===");
        for (Map.Entry<Long, Set<String>> e : mWidth.entrySet()) {
            long d = e.getKey();
            out("+0x" + Long.toHexString(d)
                + " w=" + e.getValue() + " casts=" + mCast.get(d)
                + " groups=" + mGroup.get(d) + " nFuncs=" + mFunc.get(d).size());
        }
        out("maxEnd=0x" + Long.toHexString(maxEnd) + " at " + maxEndWhere);
        out("groupC count=" + groupC.size());
        out("ambiguous count=" + amb.size());
        out("total time ms=" + (System.currentTimeMillis() - t0));
        out("[done] see EVIDENCE\\cell_fields_merged.txt / decomp_all.c / stride_0x148_sites.txt");
        log.close();
        di.dispose();
    }

    static long parse(String s) {
        s = s.trim();
        if (s.startsWith("0x") || s.startsWith("0X")) return Long.parseLong(s.substring(2), 16);
        return Long.parseLong(s);
    }
}
