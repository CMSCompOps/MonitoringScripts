#!/bin/sh

export SSTBASE=$(dirname $(readlink -f "${BASH_SOURCE[0]}"))
export CERTS=$SSTBASE/certs
export PYTHONPATH="$PYTHONPATH:$SSTBASE"

export SSTOUT="$SSTBASE/output"
if [ ! -d "$SSTOUT" ]; then
    mkdir $SSTOUT
fi
