
#th that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ./init.sh
OUT=$SSTBASE/output/metrics/productionStatus/

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

python productionStatus.py $OUT
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/productionStatus/
