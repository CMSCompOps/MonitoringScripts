
# by Luyckx S.

# This code is called by the python script. Do not call this function yourself.
# this code will add sites to the database when they are not yet included. This will be checked every time the python script is runned.

site_list_prev=$1
site_list=$2

echo "running update_sitelist.sh with site_list_prev: $site_list_prev and site_list: $site_list"


# Looping the previous voBox list and checking if all these sites are already in the site_list. If not add them
cat ${site_list_prev} | while read oldsite
do
  if `cat ${site_list} | grep "${oldsite}" 1>/dev/null 2>&1`
  then
     echo "${oldsite} already inside"
   else
     echo "will keep the old site ${oldsite} in the list"
     echo $oldsite >>  $site_list
   fi
done

# copy the new site_list to the previous site_list for the next iteration
cp $site_list $site_list_prev
