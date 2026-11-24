// W164: find callers of the big Process-candidate functions; decompile off4 subtable methods
// @category W164
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class W164_Proc2 extends GhidraScript {
    void xrefs(long t,String label)throws Exception{
        Address a=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(t);
        println("=== callers of "+label+" @"+a+" ===");
        ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(a);
        int n=0;while(it.hasNext()){Reference r=it.next();if(!r.getReferenceType().isCall())continue;
            Function cf=currentProgram.getFunctionManager().getFunctionContaining(r.getFromAddress());
            println("  call@"+r.getFromAddress()+" in "+(cf==null?"?":cf.getEntryPoint())+
                (cf==null?"":" size="+cf.getBody().getNumAddresses()));n++;}
        if(n==0)println("  (none)");
    }
    public void run()throws Exception{
        xrefs(0x004B2630L,"Drive big");
        xrefs(0x0075AEC0L,"Walk big");
        xrefs(0x004DA530L,"FootClass AI");
        // dump off4 Drive subtable methods and find which calls 0x4B2630 internally
        // off4 Drive vt=0x7E7EB0, 50 slots. Dump each slot target's direct CALLs count + whether calls 4B2630
        println("=== Drive off4 subtable slot->body direct calls to 0x4B2630? ===");
        long vt=0x007E7EB0L;
        for(int i=0;i<50;i++){
            long faddr=currentProgram.getMemory().getInt(currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(vt+4*i))&0xFFFFFFFFL;
            Address fa=currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(faddr);
            Function f=currentProgram.getFunctionManager().getFunctionContaining(fa);
            if(f==null){continue;}
            boolean has=false; int ncall=0;
            InstructionIterator ii=currentProgram.getListing().getInstructions(f.getBody(),true);
            while(ii.hasNext()){Instruction ins=ii.next();if(ins.getMnemonicString().startsWith("CALL")){ncall++;
                for(Object o:ins.getOpObjects(0)){if(o instanceof Address && ((Address)o).getOffset()==0x4B2630)has=true;}}}
            if(has||ncall>6) println("  slot "+i+" (+0x"+Integer.toHexString(4*i)+") -> "+f.getEntryPoint()+" size="+f.getBody().getNumAddresses()+" calls="+ncall+(has?" ***calls 4B2630":""));
        }
    }
}
