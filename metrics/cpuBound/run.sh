
#th that contain this script
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source ../../init.sh
OUT=$SSTBASE/output/metrics/siteReadiness

if [ ! -d "$OUT" ]; then
    mkdir -p $OUT
fi

date=$(date -I --utc -d "yesterday")
echo "Deleting old file"
rm -rf /afs/cern.ch/user/c/cmssst/www/siteReadiness/siteReadiness.txt
python dailyMetric.py $date $OUT
cp $OUT/* /afs/cern.ch/user/c/cmssst/www/siteReadiness/
