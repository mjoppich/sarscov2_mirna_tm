
import os,sys
import argparse
import glob

sys.path.append(os.path.dirname(__file__) + '/../miRExplore/python/')

from synonymes.GeneOntology import GeneOntology
from synonymes.SynfileMap import SynfileMap
from textmining.SyngrepHitFile import SyngrepHitFile
from textmining.SentenceID import SentenceID
from synonymes.SynonymFile import Synfile, AssocSynfile
from collections import defaultdict

#"META:52" "META:02689"
import pickle, glob

gene2target = defaultdict(set)

#diseaseObo = GeneOntology("/mnt/d/owncloud/data/miRExplore/doid.obo")
#diseaseTM = '/mnt/d/owncloud/data/miRExplore/textmine/aggregated_pmid/disease.pmid'
#diseaseIDs = [diseaseObo["DOID:162"]]


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-s', '--sent', type=str, nargs='+', help='an integer for the accumulator', required=True)
parser.add_argument('-o', '--obo', type=argparse.FileType("r"), default="../obodir/viral_terms.obo", required=False, help='an integer for the accumulator')

parser.add_argument('-r', '--results', type=str, default="/mnt/raidbio/biocluster/projekte/Corona2020/Texts/results.litcovid.raw/", required=False, help='an integer for the accumulator')

args = parser.parse_args()

doc2sentences = defaultdict(list)

print("Preparing obo")

oboDict = {}
termObo = GeneOntology(args.obo.name)
oboDict[0] = termObo

grp1IDs = ["MIR_FORM"]
grp2IDs = [x for x in termObo.dTerms if not x in grp1IDs]

grp3IDs = ["MIR_NAME"]

termID2group = {}
for x in grp1IDs:
    termID2group[x] = "GRP1"

for x in grp2IDs:
    termID2group[x] = "GRP2"




print("Loading sentences")

for sentFolder in args.sent:
    inputFiles =  [x for x in glob.glob(sentFolder + "/*.sent")]

    print("Processing files: {}".format(len(inputFiles)), file=sys.stderr)

    for sfid, sentFile in enumerate(inputFiles):

        if sfid % 1000 == 0:
            print("Processed file number", sfid, file=sys.stderr)

        with open(sentFile, "r") as fin:
            for line in fin:
                line = line.strip().split("\t")

                if len(line) != 2:
                    print(line,file=sys.stderr)
                    continue

                sentID = SentenceID.fromStr(line[0])
                doc2sentences[sentID.docID].append((sentID, line[1]))

print("Loading sentences finished")

foundSentences = 0

resultBase = args.results

ent1Syns = SynfileMap(resultBase +"/synfile.map")
ent1Syns.loadSynFiles(('/mnt/raidbio/biocluster/projekte/Corona2020/Texts/', "/mnt/biocluster/projekte/Corona2020/Texts/"))

searchPath = resultBase + "/*.index"
print("Search path", searchPath, file=sys.stderr)

#print(searchPath)
for syngrepfile in glob.glob(searchPath):

    ent1Hits = SyngrepHitFile(syngrepfile, ent1Syns, sentIDNoText=True)

    for docID in ent1Hits:

        ent1SynHits = ent1Hits.getHitsForDocument(docID)

        sent2termGrp2hits = defaultdict( lambda : defaultdict(list))
        docSentWithName = defaultdict( lambda : defaultdict(list))

        for hit in ent1SynHits:
            hitSyn = ent1Syns.getSynonyme(hit.synonymID)
            hitTerm = termObo[hitSyn.id]

            hitGrp = termID2group[hitTerm.id]

            if hitGrp == "MIR_NAME":
                docSentWithName[hit.documentID]["MIR_NAME"].append((hit, hitSyn, hitTerm))

            sent2termGrp2hits[hit.documentID][hitGrp].append((hit, hitSyn, hitTerm))

        foundCooc = False
        relDocSents = set()
        for sentID in sent2termGrp2hits:

            if len(sent2termGrp2hits[sentID]) >= 2:

                grp1Hits = sent2termGrp2hits[sentID]["GRP1"]
                grp2Hits = sent2termGrp2hits[sentID]["GRP2"]

                for hit1, hitSyn1, hitTerm1 in grp1Hits:
                    for hit2, hitSyn2, hitTerm2 in grp2Hits:

                        #if hit1.position[0] < hit2.position[0]:
                        #    continue

                        if abs(hit1.position[0] - hit2.position[0]) < 50:
                            print(str(sentID), hit1.foundSyn, hit2.foundSyn)
                            foundCooc = True
                            relDocSents.add(sentID)

            elif len(docSentWithName[sentID]["MIR_NAME"]) > 0:
                directHits = docSentWithName[sentID]["MIR_NAME"]
                foundCooc = True
                for dHit in directHits:
                    print(str(sentID), "DH", dHit.foundSyn, dHit.foundSyn)

                relDocSents.add(sentID)

        if foundCooc:

            for sentID, sent in doc2sentences[docID]:

                if int(sentID.parID) <= 2 or sentID in relDocSents:
                    print(sentID, sent)

            print()
            print()
            print()
            print()

            foundSentences += 1


