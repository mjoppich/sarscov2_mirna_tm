echo "Usage: runSyngrep [output] [infiles] [excludes] [synfiles]"

OUTPUT=$1
INFILE=$2
EXCL=$3

echo $OUTPUT
echo $INFILE
echo $EXCL

shift
shift
shift

SYNFILES=$@
echo $SYNFILES

SYNGREP_EXCLUDE="-e /mnt/biocluster/projekte/Corona2020/Texts/excludes/all_excludes.syn"

if [ ! -z "$EXCL" ]; then
SYNGREP_EXCLUDE=""
fi

#SYNGREP="./progs/syngrep"
SYNGREP="/usr/bin/python3 ./textmineDocument.py"
Context_SyngrepCall="$SYNGREP -np 16 -s $SYNFILES"
SYNGREP_EXTRAS="-nocells -tl 5 -prunelevel none "
#-extra '()[]' -tuple /home/proj/biosoft/SFB1123/Athero_Bioinfo.tuple

SYNGREPCALL="$Context_SyngrepCall -f "$INFILE" -o $OUTPUT $SYNGREP_EXTRAS $SYNGREP_EXCLUDE"
echo $SYNGREPCALL
/usr/bin/time --verbose $SYNGREPCALL  || exit -1

#rm $OUTPUT/*.contextes
