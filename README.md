

# Download Data

## Litcovid

https://ftp.ncbi.nlm.nih.gov/pub/lu/LitCovid/

Save to xmls_litcovid and extract to litcovid2pubtator.xml

## Pubtator

https://ftp.ncbi.nlm.nih.gov/pub/lu/PubTatorCentral/PubTatorCentral_BioCXML/

Save to xmls_pubtator and extract to xmls_pubtator/output/BioCXML/*.xml

# Extract Sentences

From main directory do the following.

This requires the following python packages: spacy, scispacy (en_core_sci_lg, v0.4.0, https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.4.0/en_core_sci_lg-0.4.0.tar.gz), lxml, pathos.

## Litcovid

`python3 splitXMLintoChunks.py litcovid2pubtator.xml xmls_litcovid_chunk/litcovid2_chunks`

`python3 extract_sentences3.py INT 32 xmls_litcovid_chunk/ &> nohup_extract_litcovid2`

## Pubtator

`python3 extract_sentences3.py INT 16 xmls_pubtator/output/BioCXML/ &> xmls_pubtator/extract_sentences.out`


# Do co-occurrence search

## Prepare viral terms

For translating the viral_terms.obo file to a valid synonym list, we use the diseaseobo2syn.py function from miRExplore:

`git clone https://github.com/mjoppich/miRExplore.git`

`mkdir -p synonyms`

We can now convert the viral_terms.obo into a synonym list

`python3 miRExplore/python/synonymes/diseaseobo2syn.py mirna_cooc/viral_terms_v1.obo mirna_cooc/viral_terms_v1.syn`

and finally text mine all extracted sentences for the viral terms:

`mkdir -p results.litcovid.raw/viral_terms/`

`bash runSyngrep.sh "./results.litcovid.raw/viral_terms/" ./xmls_litcovid_chunk/ "" ./mirna_cooc/viral_terms_v1.syn`


## Perform co-occurrence search in mirna_cooc folder for litcovid

`python3 mirna_cooc/getMIRNA_Coocs.py --sent xmls_litcovid_chunk/ --obo mirna_cooc/viral_terms_v1.obo --results results.litcovid.raw/viral_terms > mirna_cooc/identified_sentences_litcovid22`

`cut -f 1 -d' ' mirna_cooc/identified_sentences_litcovid22 | sort | uniq | grep -i "" > mirna_cooc/identified_sentences_litcovid22_sentid`

`grep -f mirna_cooc/identified_sentences_litcovid22_sentid xmls_litcovid_chunk/*.sent > mirna_cooc/rel_sentences_litcovid22`


## Getting supplemental files for open-access papers

The benefit of open access papers is, that all data (abstract, full text and )

`python3 mirna_cooc/download_europepmc_xmls.py mirna_cooc/identified_sentences_litcovid22 mirna_cooc/litcovid_xmls`

`python3 mirna_cooc/XMLtoSupplFiles.py mirna_cooc/litcovid_xmls mirna_cooc/litcovid_supplements/`



# Re-doing text mining (iteration2)

After reading through literature, identify literature through miRNA names

`python3 miRExplore/python/synonymes/diseaseobo2syn.py mirna_cooc/viral_terms_v2.obo mirna_cooc/viral_terms_v2.syn`

`mkdir -p results.litcovid.raw/viral_terms2/`

`bash runSyngrep.sh "./results.litcovid.raw/viral_terms2/" ./xmls_litcovid_chunk/ "" ./mirna_cooc/viral_terms_v2.syn`

`python3 mirna_cooc/getMIRNA_names.py --sent xmls_litcovid_chunk/ --obo mirna_cooc/viral_terms_v2.obo --results results.litcovid.raw/viral_terms2/ > mirna_cooc/identified_sentences_names_litcovid22`


