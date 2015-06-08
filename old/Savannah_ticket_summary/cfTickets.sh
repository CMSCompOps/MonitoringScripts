#!/bin/bash


fold=data/old.txt
fnew=data/new.txt
fout=data/ops.txt
fsav=data/savannah.txt

makeTable() {

    echo "update txt files?"
    read
    if [ "$REPLY" == "y" ]; then
	mv -v $fnew $fold
	wget -O $fsav http://cms-project-relval.web.cern.ch/cms-project-relval/savannah/savannah.html
	#
	sed -n '/per category/,/per squad/ p' $fsav | grep 'open tickets' | grep -v 'Summary: open' >$fnew
    fi
    sed -i -e '/^$/ d' -e '/^---------/ d' -e '/open tickets/ d' $fsav
    sed -i 's/[ \t][ \t]*/ /g' $fold
    sed -i 's/[ \t][ \t]*/ /g' $fnew

    rm -f $fout
    while read -u 7 line; do
	line=`echo "$line" | sed 's/[ \t][ \t]*/ /g'`
	if [ "$line" == "" ]; then continue; fi
	type=`echo $line | sed 's/\([^:][^:]*\):[^0-9][^0-9]*[0-9][0-9]*.*/\1/'`
	nTkt=`echo $line | sed 's/[^:][^:]*:[^0-9][^0-9]*\([0-9][0-9]*\).*/\1/'`
	oldline=`grep "$type:" $fold`
	if [ "$oldline" == "" ]; then
	    oldNTkt=0
	else
	    oldNTkt=`echo $oldline | sed 's/[^:][^:]*:[^0-9][^0-9]*\([0-9][0-9]*\).*/\1/'`
	fi
	diff=`echo "$nTkt - $oldNTkt" | bc -l`

	# get the number of days since last modified for each ticket
	nUnchanged=`sed -n "/$type/,/^[^<]/ p" $fsav | grep href | sed 's/.*days and last modified[ \t][ \t]*\([0-9][0-9]*\).*/\1/'`
	nOld=0
	for day in $nUnchanged; do
	    if (( day > 12 )); then
		(( nOld++ ))
	    fi
	done
	ages=`sed -n "/$type/,/^[^<]/ p" $fsav | grep href | sed 's/.*open since[ \t][ \t]*\([0-9][0-9]*\).*/\1/'`
	nNew=0
	for age in $ages; do
	    if (( $age < 8 )); then
		(( nNew++ ))
	    fi
	done
	
	printf "%10d  %3d   %+3d   %5d       %-30s\n" $nTkt $nNew $diff $nOld "$type">> $fout
    done 7<$fnew

    echo '<pre>'
    printf "%10s %s %s %10s                              \n" "total" "  new " " net" " unmodified"
    sort -k4 -n -r $fout
    echo '</pre>'
    url='https://dl.dropboxusercontent.com/u/57862424/CMS/CompOpsMeeting/130701/SiteReadiness/T2_SR_Combined.png'
    echo "<a href=$url><img src=\"$url\" width=\"490\"></a>"
}
makeTable
