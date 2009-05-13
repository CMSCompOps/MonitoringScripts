#!/bin/sh
cd /afs/cern.ch/cms/LCG/SiteComm

/usr/bin/python /afs/cern.ch/user/s/samcms/mybin/list-tags.py 

cat <<EOF > published-tags/AAAReadme.html
<html>
<body>
<h1> Published Tags for CMS CE's </h1>

This directory afs/cern.ch/cms/LCG/SiteComm/published-tags
contains one file for each CE that
is published in lcg-bdii.cern.ch and supports CMS VO
<p>
CE are listed by host name

<p>
Each file contains the list of CMS Runtime Tags, with
the VO-cms- suffix stripped

<p>
Those files are created by an acrontab job on lxplus.cern.ch
that runs every hour under "belforte" account and executes
<br>
<a href="list-tags.sh.txt">/afs/cern.ch/user/s/samcms/mybin/list-tags.sh</a>

<p>
all the BDII query work is done by a
<a href="list-tags.py.txt">python script</a>
kindly provided by Burt Holzman

<p>
relevant line in acrontab config file is
<pre>
30 * * * * lxplus /afs/cern.ch/user/s/samcms/mybin/list-tags.sh > /dev/null
</pre>
<p>
<small> 24 June 2008 - Stefano Belforte</small>
</html>
</body>
EOF
