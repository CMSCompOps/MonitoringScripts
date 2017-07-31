
#th that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ../../init.sh
OUT=$SSTBASE/output/metrics/xfers/

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

date=$(date --utc +"'%Y-%m-%dT%H:%M:%S'")

python xfers.py $date $OUT
cp $OUT/*.txt /afs/cern.ch/user/c/cmssst/www/xfers/
