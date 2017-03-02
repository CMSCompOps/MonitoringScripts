#!/bin/bash

my_tar_dir="$1"

cms_os=`/cvmfs/cms.cern.ch/common/cmsos`

package_url="http://cmsrep.cern.ch/cgi-bin/cmspkg/driver/cms/"

unset BUILD_ARCH
/usr/bin/python ${my_tar_dir}/tests/get_required_packages.py $cms_os $package_url
exit_code=$?
 
if [ $exit_code -ne 0 ]; then
	echo $ERROR_PACKAGE_NOT_FOUND_MSG
	exit $ERROR_PACKAGE_NOT_FOUND
fi

exit 0
