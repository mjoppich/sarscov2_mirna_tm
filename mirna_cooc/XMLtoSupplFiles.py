import glob
import os, sys
import urllib.request

from collections import defaultdict
from lxml import etree
import logging

logger = logging.getLogger('convertJatsToText')

import time


class PubmedJournal:
    def __init__(self, journal, isoabbrev):
        self.journal = journal
        self.isoabbrev = isoabbrev


class PubmedEntry:
    
    def __init__(self, pubmedId):
        self.supplements = None



    @classmethod
    def get_node_with_attrib(cls, node, path, attrib, attribvalue, default=None):
        try:
            values = [x for x in node.findall(path)]

            for idNode in values:
                if not attrib in idNode.attrib:
                    continue

                idType = idNode.attrib[attrib]

                if idType == attribvalue:
                    return idNode

            return default
        except:
            return default

    @classmethod
    def get_node_attrib(cls, node, attrib, default=None):
        try:
            if not attrib in node.attrib:
                return default
            return node.attrib[attrib]

        except:
            return default

    @classmethod
    def get_nodes_with_attrib(cls, node, path, attrib, attribvalue, default=None):
        try:
            values = [x for x in node.findall(path)]
            keepNodes = []

            for idNode in values:
                if not attrib in idNode.attrib:
                    continue

                idType = idNode.attrib[attrib]

                if idType == attribvalue:
                    keepNodes.append(idNode)

            return keepNodes
        except:
            return default

    @classmethod
    def get_node(cls, node, path, default=None):
        try:
            value = node.find(path)
            return value
        except:
            return default

    @classmethod
    def get_value_from_node(cls, node, path, default=None):
        try:
            if path != None:
                valueElem = node.find(path)
                value = valueElem.text
                return value
            else:
                return node.text
        except:
            return default

    @classmethod
    def get_inner_text_from_node(cls, node, default=[]):
        if node == None:
            return default
        texts = [x.strip() for x in node.itertext() if len(x.strip()) > 0]

        if len(texts) == 0:
            return default
        elif len(texts) == 1:
            return texts[0]
        else:
            return texts

    @classmethod
    def get_inner_text_from_path(cls, node, path, default=None):
        fnode = cls.get_node(node, path, None)
        textReturn =  cls.get_inner_text_from_node(fnode, default=default)

        if type(textReturn) == list:
            textReturn = " ".join(textReturn)
        
        return textReturn

    @classmethod
    def get_nodes(cls, node, path):
        try:
            return [x for x in node.find(path)]
        except:
            return []

    @classmethod
    def get_node_values(cls, node):
        if node == None:
            return None

        childNodes = [x for x in node]

        allValues = []

        for child in childNodes:

            value = cls.get_value_from_node(child, None, None)

            if value != None:
                allValues.append(value)

        return allValues



    @classmethod
    def get_supplements(cls, node, PMCID):

        if node == None:
            return None

        """
        <supplementary-material content-type="local-data" id="SD1">
        <label>Supplementary Information</label>
        <media xlink:href="EMS103586-supplement-Supplementary_Information.pdf" mimetype="application" mime-subtype="pdf" id="N66755" position="anchor"/>
        </supplementary-material>
        """


        pprArchiveNode = cls.get_node_with_attrib(node, "front/article-meta/article-id", "pub-id-type", "archive", None)
        pprArchive = cls.get_inner_text_from_node(pprArchiveNode)

        manuscriptNode = cls.get_node_with_attrib(node, "front/article-meta/article-id", "pub-id-type", "manuscript", None)
        manuscriptID = cls.get_inner_text_from_node(manuscriptNode)

        #<article-id pub-id-type="archive">PPR234064</article-id>
        #http://europepmc.org/api/fulltextRepo?pprId=PPR234064&type=FILE&fileName=EMS103586-supplement-Supplementary_Information.pdf&mimeType=application/pdf

        foundNodes = node.findall('.//supplementary-material/media')
        allReturnValues = []

        for mediaNode in foundNodes:
            #print(mediaNode, mediaNode.attrib)
            baseNameSuppl = cls.get_node_attrib(mediaNode, "{http://www.w3.org/1999/xlink}href", None)
            mimeTypeSuppl = cls.get_node_attrib(mediaNode, "mimetype", None)
            mimeTypeSubSuppl = cls.get_node_attrib(mediaNode, "mime-subtype", None)


            supplURL = "https://europepmc.org/articles/{pmc}/bin/{fname}".format(pmc=PMCID, fname=baseNameSuppl)
            #supplURL = "http://europepmc.org/api/fulltextRepo?pprId={pprArch}&type=FILE&fileName={fname}&mimeType={mtype}/{mtypesub}".format(
            #    pprArch = pprArchive, fname=baseNameSuppl, mtype=mimeTypeSuppl, mtypesub=mimeTypeSubSuppl
            #)

            outdict = {}
            outdict["file"] = baseNameSuppl
            outdict["mime"]=mimeTypeSubSuppl
            outdict["url"]=supplURL
            outdict["archive"]=pprArchive
            outdict["manuscript"] = manuscriptID

            allReturnValues.append(outdict)

        return allReturnValues

        

    @classmethod
    def removeLinebreaks(cls, text):

        if text == None or type(text) != str:
            return text

        text = text.replace('\n', ' ').replace('\r', '')
        return text

    @classmethod
    def fromXMLNode(cls, node):

        supplements = cls.get_supplements(node)

        return supplements

class PubmedXMLParser:

    def __init__(self):
        self.tree = None

    def remove_namespace(self, tree):
        """
        Strip namespace from parsed XML, assuming there's only one namespace per node
        """
        if tree == None:
            return

        for node in tree.iter():
            try:
                has_namespace = node.tag.startswith('{')
            except AttributeError:
                continue  # node.tag is not a string (node is a comment or similar)
            if has_namespace:
                node.tag = node.tag.split('}', 1)[1]

    def parseXML(self, path):

        self.tree = None

        try:
            self.tree = etree.parse(path)
        except:
            try:
                self.tree = etree.fromstring(path)
            except Exception as e:
                eprint("Unable to load graph:", str(e))
                raise
        if '.nxml' in path:
            self.remove_namespace(self.tree)  # strip namespace for

        return self.tree

class PubmedArticleIterator:

    def __init__(self, parser):
        self.parser = parser

    def __iter__(self):

        if self.parser == None:
            return self

        return self.parser.tree.findall('article').__iter__()

    def __next__(self):
        raise StopIteration()


"""

python3 ~/python/miRExplore/python/textmining/downloadPubmedAbstracts.py
python3 medlineXMLtoStructure.py
python3 removeDuplicateSentences.py

"""
import pdftotext

def extractPDF(infile, outfile, supplInfo):
    with open(infile, "rb") as f, open(outfile, "w") as fout:
        pdf = pdftotext.PDF(f)
        pdfStr = "\n\n".join(pdf)

        #doc = nlp(pdfStr)
        #sents = [x.text for x in doc.sents]

        sents = [x for x in pdfStr.split("\n") if len(x) > 0]

        manuscriptName = supplInfo["manuscript"]

        for sentNum,sent in enumerate(sents):
            print("{}\t{}".format("{}.suppl{}.{}".format(manuscriptName, supplInfo["supnum"], sentNum), sent), file=fout)

import pandas as pd

def extractXLSX(infile, outfile, supplInfo):
    with open(outfile, "w") as fout:
        
        inExcel = pd.read_excel(infile, sheet_name=None)

        if type(inExcel) in [dict]:
            allExcelStrs = []
            for shName in inExcel:
                allExcelStrs.append( inExcel[shName].to_string() )

            excelStr = "\n".join(allExcelStrs)
        else:
            excelStr = inExcel.to_string()

        sents = [x for x in excelStr.split("\n") if len(x) > 0]
        manuscriptName = supplInfo["manuscript"]

        for sentNum,sent in enumerate(sents):
            print("{}\t{}".format("{}.suppl{}.{}".format(manuscriptName, supplInfo["supnum"], sentNum), sent), file=fout)

import pypandoc

def extractWord(infile, outfile, supplInfo):
    
    docXStr = pypandoc.convert_file(infile, 'asciidoc')
    with open(outfile, "w") as fout:

        #sents = [x for x in nlp(docXStr)]
        sents = [x.strip() for x in docXStr.split("\n") if len(x.strip()) > 0]
        manuscriptName = supplInfo["manuscript"]

        for sentNum,sent in enumerate(sents):
            print("{}\t{}".format("{}.suppl{}.{}".format(manuscriptName, supplInfo["supnum"], sentNum), sent), file=fout)


def downloadSupplement(supplementInfo, entryStoragePath):
    targetFile = os.path.join(entryStoragePath, "{}_{}".format(supplementInfo["manuscript"], supplementInfo["file"]))
    print(supplementInfo, entryStoragePath, targetFile)

    wasInLoop = False
    while not os.path.exists(targetFile):
        wasInLoop = True
        try:
            urllib.request.urlretrieve(supplementInfo["url"], targetFile)
        except:
            print("Download failed", supplementInfo["url"])

        print("Waiting some time ....")
        time.sleep(2.4)

    if not wasInLoop:
        print("Skipping", supplementInfo["url"])

    supplMime = os.path.splitext(targetFile)[1].split(".")[1].lower()
    sentFile = os.path.splitext(targetFile)[0]  + ".sent"

    print(supplMime)

    try:

        if supplMime == "pdf":
            extractPDF(targetFile, sentFile, supplementInfo)
        elif supplMime in ["xlsx", "vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            extractXLSX(targetFile, sentFile, supplementInfo)
        elif supplMime in ["docx", "vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            extractWord(targetFile, sentFile, supplementInfo)

    except:
        pass

if __name__ == '__main__':

    #nltk.data.path.append("/mnt/d/dev/nltk_data/")

    assert(len(sys.argv) == 3)
    storagePath = sys.argv[2]

    if not os.path.isdir(storagePath):
        os.mkdir(storagePath) 

    allXMLFiles = [y for x in os.walk(sys.argv[1]) for y in glob.glob(os.path.join(x[0], '*.xml'))]

    print("Found", len(allXMLFiles), "files")
    print("Going through", len(allXMLFiles), " files.")


    totalDocCount = 0

    def senteniceFile(filenames):

        totalDocCount = 0
        for filename in filenames:
            print(filename)

            
            try:
                pubmedParser = PubmedXMLParser()
                pubmedParser.parseXML(filename)
            except:
                print("Error Loading File", filename)
                continue

            elem = pubmedParser.tree.getroot()

            pmcid = os.path.splitext(os.path.basename(filename))[0]
            supplements = PubmedEntry.get_supplements(elem, pmcid)

            if supplements == None:
                print("Error Loading Article in", filename)
                continue

            totalDocCount += 1


            for sid, supplement in enumerate(supplements):

                print(sid, supplement)

                entryStoragePath = os.path.join(storagePath, pmcid)
                if not os.path.isdir(entryStoragePath):
                    os.mkdir(entryStoragePath)


                supplement["manuscript"] = pmcid
                supplement["supnum"] = sid

                downloadSupplement(supplement, entryStoragePath)



        print(totalDocCount)

    senteniceFile(allXMLFiles)