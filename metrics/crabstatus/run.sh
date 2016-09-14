
#th that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ../../init.sh
OUT=$SSTBASE/output/metrics/crabstatus/

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

python crabstatus.py $OUT
cp $OUT/*.txt /afs/cern.ch/user/c/cmssst/www/crabstatus/ 
