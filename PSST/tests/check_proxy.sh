#!/bin/bash

#check if openssl is installed
# if [ -x "/usr/bin/openssl" ]; then
# 	echo `openssl version`
# else
# 	echo $ERROR_NO_OPENSSL_MSG
# 	exit $ERROR_NO_OPENSSL
# fi

voms_server=`voms-proxy-info --uri`
echo "VOMS server: ${voms_server}"


# Checking some X509 details
if [ -e "$X509_CERT_DIR" ]; then
	cert_dir=$X509_CERT_DIR
elif [ -e "$HOME/.globus/certificates/" ]; then
	  cert_dir=$HOME/.globus/certificates/
elif [ -e "/etc/grid-security/certificates/" ]; then
	cert_dir=/etc/grid-security/certificates/
else
	echo $ERROR_NO_CERT_DIR_MSG
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
