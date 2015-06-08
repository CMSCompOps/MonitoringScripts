<?php

	$host = "dbod-ssdb.cern.ch:5501";
	$user = "admin";
	$pass = "Ch4ng3m3_07042014";
	$dbname = "ssdb";
	
	$connect   = mysql_connect($host , $user , $pass) or die(mysql_error());
	$selectDb = mysql_select_db($dbname , $connect);
	
	if(!$connect)
		{
			echo '<font color = "#900">Connection Error.</font>';					
		}
	else
		{
			if(!$selectDb)
				{
					echo '<font color = "#900">Database Error.</font>';					
				}
		}
?>