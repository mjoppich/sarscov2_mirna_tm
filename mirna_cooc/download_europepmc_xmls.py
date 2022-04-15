

import sys
from pynvim import encoding

import requests
import yaml
import shutil
import json
import os


allDocIDs = set()

with open(sys.argv[1]) as fin:



    for line in fin:

        line = line.strip()

        if len(line) == 0:
            continue

        line = line.split(" ", 1)

        if len(line) != 2:
            continue

        sentID = line[0]

        if not sentID[0].isdigit():
            continue

        sentID = sentID.split(".")[0]

        allDocIDs.add(sentID)


print(allDocIDs)



def get_europepmcs_xml(docid):


    xmlURL = "https://www.ebi.ac.uk/europepmc/webservices/rest/{}/fullTextXML".format(docid)

    with requests.get(xmlURL) as r, open("{}/{}".format(sys.argv[2], docid + ".xml"), 'w') as out_file:
        out_file.write(r.text)




def get_pmid_xml(docid):

    xmlURL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=ext_id:{}%20src:MED&format=json".format(docid)

    with requests.get(xmlURL) as r:
        docInfo = r.content
        docJson = yaml.safe_load(docInfo)

        try:
            if docJson["hitCount"] > 0:

                if "pmcid" in docJson["resultList"]["result"][0]:
                    PMCid = docJson["resultList"]["result"][0]["pmcid"]

                    return get_europepmcs_xml(PMCid)
                else:
                    print(docJson["resultList"]["result"])

        except:
            print(docJson)
            exit(-1)

if not os.path.exists(sys.argv[2]):
    os.makedirs(sys.argv[2], exist_ok=True)

for x in allDocIDs:

    if len(x) == 7:

        get_europepmcs_xml("PMC" + x)

    elif len(x) == 8:

        get_pmid_xml(x)
