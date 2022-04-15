from lxml import etree
import sys

inputXML = sys.argv[1]

print("Parsing documents")
sys.stdout.flush()
tree = etree.parse(inputXML)

print("Finding all documents")
sys.stdout.flush()
docTree = [x for x in tree.findall("document")]

from itertools import zip_longest
def group_elements(n, iterable, padvalue=None):
    return zip_longest(*[iter(iterable)]*n, fillvalue=padvalue)

print("Splitting all documents")
sys.stdout.flush()
chunk_size = 1000

outputbase = sys.argv[2]

for i in range(0, len(docTree), chunk_size):

    print(i)

    outputFile = "{}_{}.xml".format(outputbase, i)

    savechunk = docTree[i:i+chunk_size]

    root = etree.Element("collections")

    for x in savechunk:
        root.append(x)
    et = etree.ElementTree(root)
    et.write(outputFile, pretty_print=True)