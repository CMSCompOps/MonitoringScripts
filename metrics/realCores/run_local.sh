cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source init.sh
OUT=$SSTBASE/output/metrics/realCores

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

python realCores.py $OUT
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/realCores/
