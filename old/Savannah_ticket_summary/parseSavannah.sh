#!/bin/bash
webdir=$HOME/www/savannah
mkdir -p $webdir
./parseSavannah.py                  -o $webdir/savannah.html                          &
./savannahStatistics.py --days 7    -o $webdir/savannah_statistics_last_7_days.html   &
./savannahStatistics.py --days 30   -o $webdir/savannah_statistics_last_30_days.html  &
./savannahStatistics.py --days 365  -o $webdir/savannah_statistics_last_year.html     &
./savannahStatistics.py --days 9999 -o $webdir/savannah_statistics_2011_2012.html     &
./savannahSummary.py    --days 365  -o $webdir/savannah_summary_last_year.html        &  
