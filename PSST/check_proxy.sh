#!/usr/bin/env bash

#check if openssl is installed
if [ -x "/usr/bin/openssl" ]; then
	echo `openssl version`
else
	echo $ERROR_NO_OPENSSL_MSG
	exit $ERROR_NO_OPENSSL
fi

voms_server=`voms-proxy-info --uri`
echo "VOMS server: ${voms_server}"

#check if voms server is available
# if ping -q -c 1 -W 1 lcgvoms25.cern.ch >/dev/null; then
# 	echo "The network is up and CMS voms server is available"
# elif ping -q -c 1 -W 1 voms24.cern.ch >/dev/null; then
# 	echo "The network is up and CMS voms server is available"
# else
# 	echo $ERROR_VOMS_SERVER_NOT_AVAILABLE_MSG
# 	exit $ERROR_VOMS_SERVER_NOT_AVAILABLE
# fi

# echo -e "GET http://lcgvoms25.cern.ch HTTP/1.0\n\n" | nc lcgvoms25.cern.ch 22 > /dev/null 2>&1
# if [ $? -eq 0 ]; then
# 	echo "VOMS server is reachable"
# else 
# 	echo $ERROR_VOMS_SERVER_NOT_AVAILABLE_MSG
# 	exit $ERROR_VOMS_SERVER_NOT_AVAILABLE
# fi

# Checking some X509 details
if [ -e "$X509_CERT_DIR" ]; then
	cert_dir=$X509_CERT_DIR
elif [ -e "$HOME/.globus/certificates/" ]; then
	  cert_dir=$HOME/.globus/certificates/
elif [ -e "/etc/grid-security/certificates/" ]; then
	cert_dir=/etc/grid-security/certificates/
else
	$ERROR_NO_CERT_DIR_MSG
	exit $ERROR_NO_CERT_DIR
fi
echo "CertDir: $cert_dir"

if [ -a "$X509_USER_PROXY" ]; then
	proxy=$X509_USER_PROXY
elif [ -a "/tmp/x509up_u`id -u`" ]; then
	proxy="/tmp/x509up_u`id -u`"
else
	echo $ERROR_NO_X509_PROXY_MSG
	exit $ERROR_NO_X509_PROXY
fi
echo "Proxy: $proxy"

# # Check proxy copy as in glidein pilots
# local_proxy_dir=~/ticket
# mkdir $local_proxy_dir &>/dev/null
# if [ $? -ne 0 ]; then
# 	echo "ERROR: could not find create $local_proxy_dir"
# 	echo "summary: CANT_CREATE_DIR"
# 	echo $ERROR_NO_PROXY_DIR 1>&2
# 	exit 1
# fi
# cp $X509_USER_PROXY $local_proxy_dir/myproxy &>/dev/null
# if [ $? -ne 0 ]; then
# 	echo "ERROR: could not copy proxy $X509_USER_PROXY"
# 	echo "summary: NO_COPY_PROXY"
# 	echo $ERROR_X509_USER_PROXY_CP 1>&2
# 	exit 1
# fi

# if [ -d "$local_proxy_dir" ]; then
# 	rm -rf $local_proxy_dir &>/dev/null
# fi

type -t voms-proxy-info
result=$?
if [ $result -eq 0 ] ; then
	isvoms=1
	echo -n "UserDN: "
	voms-proxy-info -identity
	l=`voms-proxy-info -timeleft`
	echo "Timeleft: $l s"
	fqan=`voms-proxy-info -fqan`
	echo "FQAN:"
	echo "$fqan"
else
	isvoms=0
	echo "WARNING: voms-proxy-info not found"
fi
if [ $isvoms -eq 1 -a $l -lt 21600 ] ; then
	echo "WARNING: proxy shorther than 6 hours"
fi    
exit 0
