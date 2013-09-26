
# by Luyckx S.

# This code is called by the python script. Do not call this function yourself.
# this code will add sites to the database when they are not yet included. This will be checked every time the python script is runned.

site_list_prev=$1
site_list=$2

echo "running update_voBoxlist.sh with site_list_prev: $site_list_prev and site_list: $site_list"
echo "previous sitelist:"
cat $site_list_prev
echo "==========================================="
echo "sitelist before changes:"
cat $site_list
echo "==========================================="

# Looping the previous voBox list and checking if all these sites are already in the site_list. If not add them
cat ${site_list_prev} | while read oldsite
do
  echo "debating: $oldsite"

  if `cat ${site_list} | grep "${oldsite}" 1>/dev/null 2>&1`
  then
     echo "${oldsite} already inside"
   else
     echo "will keep the old site ${oldsite} in the list"
     echo $oldsite >>  $site_list
   fi
done
echo "=========================================="
echo "sitelist after changes:"
cat $site_list
echo "=========================================="
# copy the new voBox_list to the previous voBox_list for the next iteration
cp $site_list $site_list_prev
