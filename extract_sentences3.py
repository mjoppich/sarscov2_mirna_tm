from importlib.machinery import all_suffixes
import os, sys

import time
import sys
import os
from collections import Counter


from pathos import multiprocessing as mp

import itertools
from collections import OrderedDict

from lxml import etree

#import nltk.data
#tokenizer_loc = 'tokenizers/punkt/english.pickle'
#tokenizer = nltk.data.load(tokenizer_loc)

import spacy
import scispacy
import glob


class MapReduce:

    def __init__(self, procs = 4):
        self.pool = None
        self.nprocs = procs

    def exec(self, oIterable, oFunc, sEnvironment, chunkSize = 1, pReduceFunc = None):

        self.pool = mp.ProcessPool(self.nprocs)
        allResults = []

        resultObj = None

        for x in self.chunkIterable(oIterable, chunkSize):
            allResults.append( self.pool.apipe( oFunc, x, sEnvironment ) )

        self.pool.close()

        while len(allResults) > 0:

            i=0
            while i < len(allResults):

                if allResults[i].ready():

                    result = allResults[i].get()

                    if pReduceFunc != None:

                        resultObj = pReduceFunc(resultObj, result, sEnvironment)

                    else:

                        if resultObj == None:
                            resultObj = []

                        resultObj.append(result)

                    del allResults[i]

                else:
                    i += 1

            time.sleep(0.5)

        self.pool.join()
        self.pool.clear()

        return resultObj



    @classmethod
    def chunkIterable(cls, iterable, size):

        it = iter(iterable)
        item = list(itertools.islice(it, size))

        while item:
            yield item
            item = list(itertools.islice(it, size))


class DocInfo:

    def __init__(self, id, sec2text):

        self.id = id
        self.sec2text = sec2text

    def _makeSentences(self, content):

        returns = []

        for x in content:

            doc = nlp(x)
            sents = [x.text for x in doc.sents]
            returns += sents

        return returns

    def _prepareSentences(self, articleName, module, sents):

        iSent = 1
        outContent = []

        for x in sents:

            if x == None:
                continue

            x = x.strip()
            #x = x.strip(',.;')

            if len(x) > 0:

                content = str(articleName) + "." + str(module) + "." + str(iSent) + "\t" + str(x)
                if not content[-1] == ".":
                    content += "."

                outContent.append(content)
                iSent += 1

        return outContent

    def to_sentences(self):

        if self.id == "33686269":
            for x in self.sec2text:
                print(x, self.sec2text[x])

        titleSents = self._makeSentences(self.sec2text.get("article-title", []) + self.sec2text.get("TITLE", []))
        abstractSents = self._makeSentences(self.sec2text.get("ABSTRACT", [])) #hier gibt es glaube ich kein ganzes abstract, nur aufgeteilt auf die abschnitte unten
        textSents = self._makeSentences(
            self.sec2text.get("Background", [])+self.sec2text.get("INTRO", [])+
            self.sec2text.get("RESULTS", [])+
            self.sec2text.get("CASE", [])+
            self.sec2text.get("DISCUSS", [])+
            self.sec2text.get("METHODS", [])+
            self.sec2text.get("CONCL", []) +
            self.sec2text.get("TYPETEXT", [])
            )

        supplSents = self._makeSentences(
            self.sec2text.get("SUPPL", [])+
            self.sec2text.get("FIG", [])+self.sec2text.get("TAB", [])+self.sec2text.get("TABLE", [])
        )

        finalSents = []
        finalSents += self._prepareSentences(self.id, 1, titleSents)
        finalSents += self._prepareSentences(self.id, 2, abstractSents)
        finalSents += self._prepareSentences(self.id, 3, textSents)
        finalSents += self._prepareSentences(self.id, 4, supplSents)

        return finalSents

def get_node( node, path, default=None):
    try:
        value = node.find(path)
        return value
    except:
        return default

def get_value_from_node(node, path, default=None):
    try:
        if path != None:
            valueElem = node.find(path)
            value = valueElem.text
            return value
        else:
            return node.text
    except:
        return default

def get_inner_text_from_node( node, default=[]):
    if node == None:
        return default
    texts = [x.strip() for x in node.itertext() if len(x.strip()) > 0]

    if len(texts) == 0:
        return default
    elif len(texts) == 1:
        return texts[0]
    else:
        return texts

def get_inner_text_from_path( node, path, default=None):
    fnode = get_node(node, path, None)
    return get_inner_text_from_node(fnode, default=default)


def getTextFromNodes(nodelist):
    return [x.text for x in nodelist]

def get_inner_text_from_nodes(nodelist):
    if len(nodelist) == 0:
        return ""

    joinlist = [get_inner_text_from_node(x, "") for x in nodelist]
    try:
        return " ".join(joinlist)
    except:
        print(nodelist, joinlist, [x.text for x in nodelist])

def doc2sentences(doc):

    all_section_types = Counter()

    docID = get_inner_text_from_node(doc.find(".//id")).replace(" ", "_")
    docItems = []

    sectionType = "ABSTRACT"

    for x in doc.xpath(".//offset"):
        sectionText = get_inner_text_from_nodes(x.xpath("./following-sibling::text"))
        sectTypes = getTextFromNodes(x.xpath("./preceding-sibling::infon[@key='section_type']"))
        
        if len(sectTypes) > 0:
            sectionType = sectTypes[-1]
        else:

            def type2sectiontype(x):
                if x == "front":
                    return "TITLE"
                elif x.startswith("abstract"): # abstract, abstract_title_1
                    return "ABSTRACT"
                elif x.startswith("title"): #title_1, title_2
                    return "TITLE" # this seems to be title for PMIDs
                elif x == "paragraph": #paragraph
                    print("TYPETEXT", "paragraph", x)
                    return "TYPETEXT"
                elif x == "footnote":
                    return "REF"
                elif x == "ref":
                    return "REF"
                elif x.startswith("tab"):
                    return "TABLE"
                elif x.startswith("fig"):
                    return "FIG"
                
                print(docID, "Unknown section type:", x)
                return "UNKNOWN"

            typeLabels = getTextFromNodes(x.xpath("./preceding-sibling::infon[@key='type']"))
            sectionTypeLabels = [type2sectiontype(x) for x in typeLabels]

            sectionType = sectionTypeLabels[-1]

        #print(sectionType)
        #print(sectionText)

        if sectionType == "TYPETEXT":
            print(docID, sectionType, sectionText)

        all_section_types[sectionType] += 1
        
        docItems.append((sectionType, sectionText))

    allText = OrderedDict()
    for section, texts in docItems:

        if not section in allText:
            allText[section] = []

        allText[section].append(texts)

    dI = DocInfo(docID, allText)

    docSents = dI.to_sentences()

    return docSents, allText.get("TITLE", ""), all_section_types


#hier der neue teil für metadaten:

def unlistfirst(inlist):
    if len(inlist) == 0:
        inlist = ""
    else:
        inlist = inlist[0]
    return inlist


def doc2meta(doc, title):
    metadict = OrderedDict()
    docID = get_inner_text_from_node(doc.find(".//id")).replace(" ", "_")
    year = unlistfirst([get_inner_text_from_node(x, "") for x in doc.xpath(".//infon[@key='year']")])
    journalTitle = unlistfirst([get_inner_text_from_node(x, "") for x in doc.xpath(".//infon[@key='journal-title']")])
    pmidID = unlistfirst([get_inner_text_from_node(x, "") for x in doc.xpath(".//infon[@key='article-id_pmid']")])
    pmcID = unlistfirst([get_inner_text_from_node(x, "") for x in doc.xpath(".//infon[@key='article-id_pmc']")])
    doiID = unlistfirst([get_inner_text_from_node(x, "") for x in doc.xpath(".//infon[@key='article-id_doi']")])    
    authorNamesInit = [get_inner_text_from_node(x, ";") for x in doc.xpath("./passage[1]")[0].xpath(".//infon[starts-with(@key,'name_')]")]

    authorNames = set()
    for aname in authorNamesInit:
        authorDict = set()
        for aaname in aname.split(";"):
            splitName = tuple(aaname.split(":"))
            if len(splitName) != 2:
               print("Strange Name", docID, aaname)  
            authorDict.add(splitName)
        authorNames.add( tuple(authorDict) )

    if len(authorNames) == 0:
        #Farhadi A, Bagherzadeh R, Moradi A, Nemati R, Sadeghmoghadam L,
        allAuthorNames = ", ".join([get_inner_text_from_node(x, "") for x in doc.xpath(".//infon[@key='authors']")])
        for author in allAuthorNames.split(", "):
            aauthor = author.split(" ")

            for aname in aauthor:
                if len(aname) == 0:
                    continue
                authorNames.add( ("given-names", aname) )
                break

    indirectDOI = False
    if doiID == "":
        
        try:
            doiID = unlistfirst([get_inner_text_from_node(x, "") for x in doc.xpath(".//infon[@key='journal']")])    
            doiID = doiID.split("doi:")[1].split(" ")[0]
            indirectDOI=True
        except:
            pass
        


    metadict["docID"] = docID
    metadict["year"] = year
    metadict["journalTitle"] = journalTitle
    metadict["pmidID"] = pmidID
    metadict["pmcID"] = pmcID
    metadict["doiID"] = doiID
    metadict["indirectDOI"] = str(indirectDOI)
    metadict["num_authors"] = str(len(authorNames))
    metadict["authors"] = str(authorNames)
    metadict["title"] = str(title)
    return metadict



if __name__ == '__main__':

    def processFile(outputSents, outputMeta, processDocs):

        all_section_types = Counter()

        with open(outputSents, "w", encoding="utf-8") as fout, open(outputMeta, "w", encoding="utf-8") as foutMeta:
            for docID, doc in enumerate(processDocs):
                
                docSents, docTitle, docSections = doc2sentences(doc)

                for x in docSections:
                    all_section_types[x] += docSections[x]

                docMetas = doc2meta(doc, docTitle)
                for line in docSents:
                    print(line, file=fout)
                print("\t".join(docMetas.values()), file=foutMeta)


                fout.flush()
                foutMeta.flush()

        print(outputSents)
        print(all_section_types)


    def senteniceFile(inputXMLList, env):

        all_section_types = Counter()

        for inputXML in inputXMLList:

            try:
                outputSents = os.path.splitext(inputXML)[0] + ".sent"
                outputMeta = os.path.splitext(inputXML)[0] + ".meta"
                print(inputXML, outputSents)

                #if os.path.exists(outputSents) and os.path.getsize(outputSents) > 0:
                #    print("Already processed", inputXML, outputSents)
                #    continue

                tree = etree.parse(inputXML)
                docTree = tree.findall("document")

                processFile(outputSents=outputSents, outputMeta=outputMeta, processDocs=docTree)

                print("Done", inputXML, outputSents)
            except:
                print("Error loading XML", inputXML, file=sys.stderr)

        print(all_section_types)

        return None

    def senteniceDocs(inputDocs, env):
        
        baseOutput = "{}_{}".format(env["output"], inputDocs[0])
        outputSents = baseOutput + ".sent"
        outputMeta = baseOutput + ".meta"

        try:
            processFile(outputSents=outputSents, outputMeta=outputMeta, processDocs=inputDocs[1])
        except:
            print("Error processing chunk", inputDocs[0])
            sys.stdout.flush()



    print("Loading spacy model:", sys.argv[1])

    if sys.argv[1].upper() == "INT":
        sys.argv[1] = "/mnt/f/spacy/en_ner_bionlp13cg_md-0.2.4/en_ner_bionlp13cg_md/en_ner_bionlp13cg_md-0.2.4"
        sys.argv[1] = "/mnt/biocluster/projekte/Corona2020/Texts/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0"

    print("Loading spacy model:", sys.argv[1])


    nlp = spacy.load(sys.argv[1])
    inputXMLs = sorted(set([x for x in glob.glob(sys.argv[3] + "/*.xml")] + [x for x in glob.glob(sys.argv[3] + "/*.XML")])) #sys.argv[2:]
    #inputXMLs = sys.argv[3:]#[x for x in glob.glob(sys.argv[3] + "/*.xml")] #sys.argv[2:]
    print("Processing", len(inputXMLs), "XML files")


    print("Loading XML")

    ll = MapReduce(int(sys.argv[2]))

    result = ll.exec( inputXMLs, senteniceFile, None, 1, None)

    print("Done")
