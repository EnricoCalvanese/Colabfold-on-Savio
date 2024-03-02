#importing Biopython
import Bio
import os
#import seqIO to parse through sequence files
from Bio import SeqIO
#imports for writing fasta files
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
#get the list of enriched protein sequences and parse through it with
#the SeqIO parse function
IMB2 = SeqRecord(Seq("""MAATAVVWQPRDDGLAEICSLLEQQISPSSVVDKSQIWKQLQHFSQFPDFNNYLVFILVRAEGKSVEVRQAAGLLLKNNLRGAYPSMTQENQKYIKSELLPCLGAADRNIRTTVGTIISVIVNIEGVSGWHELLPALVTCLDSNDLNHMDGAMDALSKICEDIPHVLDTEVPGLAERPINIFLPRLLQFFQSPHASLRKLALGSVNQYIIIMPAVIWQALYNSLDKYLQGLFVLANDPVPEVRKLVCAAFVHLTEVLPSSIEPHLRNVMEYMLQVNRDPDEEVSLEACEFWSAYCDAQLPPENLKEFLPRLIPVLLENMAYADDDESLLDAEEDESQPDRDQDLKPRFHTSRLHGSEDFDDDDDDSFNVWNLRKCSAAAIDVLSNVFGDEILPALMPLIQKNLSASGDEAWKQREAAVLALGAIAEGCMNGLYPHLSEIVAFLLPLLDDKFPLIRSISCWTLSRFGKYLIQESGNPKGYEQFEKVLMGLLRRLLDTNKRVQEAACSAFATVEEDAAEELVPHLGVILQHLMCAFGKYQRRNLRIVYDAIGTLADSVREELNKPAYLEILMPPLVAKWQQLSNSDKDLFPLLECFTSISQALGVGFAPFAQPVFQRCMDIIQLQQLAKVNPASAGAQYDREFIVCSLDLLSGLAEGLGSGIESLVQQSNLRDLLLNCCIDEAADVRQSAFALMGDLARVFPVYLQPRLLDFLEIASQQLSANLNRENLSVANNACWAIGELAVKVRQEVSPIVAKVVSSLGLILQHGEGVNKALVENSAITLGRLAWIRPDLVAPHMDHFMKPWCMALSMVRDDIEKEDAFRGLCAVVKVNPSGGVSSLVFICQAIASWHEIRSEDVQTEVSQVLNGYKHMLGNSWAECLSALDPPVKERLARYQV"""),
                 id="AT2G16950", name="IMB2")

#Warning: before running these next lines make sure to be in the final destination directory
os.chdir('/global/scratch/users/enricocalvane/IMB2ColabFold/fastas')
for seq_record in SeqIO.parse("AllRPs.fasta", "fasta"):
    newseq=seq_record.seq.replace("*", "")
    comb=IMB2.seq+":"+newseq
    combname=IMB2.id+"_"+seq_record.id
    os.system(f"mkdir {combname}")
    with open (combname + "/" + combname + ".fasta", "w") as o:
        o.write(f">{combname}\n{comb}")

    
