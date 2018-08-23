#!/bin/bash
cd $(dirname $(readlink -f "${BASH_SOURCE[0]}"))
source init.sh
OUT=$SSTBASE/output/metrics/ftslinks

if [ ! -d "$OUT" ]; then
      mkdir -p $OUT
    fi

date=$(date "+%Y-%m-%dT%H:%M:%SZ" --utc -d "15 minutes ago")

python eval_fts.py $date
