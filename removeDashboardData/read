python deleteSiteInfo.py -c 154 -s T2_RU_RRC_KI -f "2015-01-01" -t "2015-02-02" 
where -c is the column from which you wish to delete data -s is the site and -f and -t are from and to dates in which to delete the data. follow the steps and it'll create a file named dataToDelete.txt. Then create an unencrypted copy of your key at .globus with
openssl rsa -in  ~/.globus/userkey.pem -out  ~/.globus/unencr_key.pem
and finally
cat datatoDelete.txt | xargs -n 1 curl -k -H "Accept : application/json" -X GET --cert ~/.globus/usercert.pem --key ~/.globus/unencr_key.pem
That last step actually deletes the data, using the unencrypted cert for authentication with the dashboard web service.
