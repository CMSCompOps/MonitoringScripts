cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source init.sh
OUT=$SSTBASE/output/metrics/cpuBound

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

python cpuBound.py $OUT
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/cpuBound/
