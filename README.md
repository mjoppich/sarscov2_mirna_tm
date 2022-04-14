# SARS-CoV-2 miRNA Text Mining

## Download Data

### Litcovid

https://ftp.ncbi.nlm.nih.gov/pub/lu/LitCovid/

Save to xmls_litcovid and extract to xmls_litcovid/litcovid2pubtator.xml

### Pubtator

https://ftp.ncbi.nlm.nih.gov/pub/lu/PubTatorCentral/PubTatorCentral_BioCXML/

Save to xmls_pubtator and extract to xmls_pubtator/output/BioCXML/*.xml

## Extract Sentences

From main directory do the following.

This requires the following python packages: spacy, scispacy (en_core_sci_lg, v0.4.0, https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.4.0/en_core_sci_lg-0.4.0.tar.gz), lxml, pathos.

### Litcovid

`python3 extract_sentences3.py INT 2 xmls_litcovid/ > nohup_extract_litcovid`

### Pubtator

`python3 extract_sentences3.py INT 16 xmls_pubtator/output/BioCXML/ > xmls_pubtator/extract_sentences.out`

## Do co-occurrence search

### Prepare viral terms

For translating the viral_terms.obo file to a valid synonym list, we use the diseaseobo2syn.py function from miRExplore:

`git clone https://github.com/mjoppich/miRExplore.git`

`mkdir -p synonyms`

We can now convert the viral_terms.obo into a synonym list

`python3 miRExplore/python/synonymes/diseaseobo2syn.py obodir/viral_terms.obo synonyms/viral_terms.syn`

and finally text mine all extracted sentences for the viral terms:

`mkdir -p results.litcovid.raw/viral_terms/`
`bash runSyngrep.sh "./results.litcovid.raw/viral_terms/" ./xmls_litcovid/ "" ./synonyms/viral_terms.syn`


### Perform co-occurrence search in mirna_cooc folder for litcovid

`python3 getMIRNA_Coocs.py --sent ../xmls_litcovid/*.sent --obo ../obodir/viral_terms.obo --results /mnt/raidbio/biocluster/projekte/Corona2020/Texts/results.litcovid.raw/ > identified_sentences_litcovid22`

`cut -f 1 -d' ' identified_sentences_litcovid22 | sort | uniq | grep -i "" > identified_sentences_litcovid22_sentid`

`grep -f identified_sentences_litcovid22_sentid ../xmls_litcovid/litcovid2pubtator.sent > rel_sentences_litcovid22`


### Getting supplemental files for open-access papers

The benefit of open access papers is, that all data (abstract, full text and )


