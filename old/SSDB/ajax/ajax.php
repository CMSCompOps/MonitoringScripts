<?php
	require ("../data/connect.php");
	include ("../lib/date.class.php");
	$operation = new calculate();
	
	if($_GET){
	$operations = $_GET['operation'];
/********************************************************************************************************/
	if($operations == 'saveTwiki'){
		
		$section = $_GET['section'];
		
		$sql = ($section = 'morgue') ? "SELECT * FROM wr where morgue = 'x' order by siteName ASC" : "SELECT * FROM wr where morgue = '' order by siteName ASC"; 
		$fileName = ($section = 'morgue') ? "morguetwiki.txt" : "wrtwiki.txt";
		$query   = mysql_query($sql);
		if(mysql_affected_rows() > 0){
			
			$twikicode[] ='| *Count* | *Site* | *In* | *Out* | *Total Week* | *Exit Code (SAM)* | *Exit Code (HC)* | *Links* | *Ticket Number* | *No reply* |';
			$count = 0;
			while($veri = mysql_fetch_array($query))
				{
					$count++;
					$twikicode[] = '| '.$count.' | '.$veri[1].' | '.$operation->datecompare($veri[2]).' | '.''.' | '.$operation->calculateTotalWeek($veri[1] , $veri[2]).' | '.$operation->calculateFailTest("sam" , $veri[0] , "on").' | '.$operation->calculateFailTest("hc" , $veri[0] , "on").' | '.$operation->calculateFailTest("links" , $veri[0] , "on").' | '.'[['.$veri[5].']['.$veri[4].']] |' . ' |';     
				 }
				
			$fh = fopen($fileName, 'w') or die("can't open file");
			
			foreach ($twikicode as $twikiLine) 
				{
					$value = $twikiLine . "\n";
					fwrite($fh, $value);
				}
			fclose($fh);
		}
			
		$array["ok"] = $section;
		echo json_encode($array);
		
		}
	}
	
	if($_POST)
		{
			/**************************Read data from form by Script*********************************/
			$operations = $_POST['operation'];
/********************************************************************************************************/

		if($operations == 'saveTwiki'){
			
		$sql = "SELECT * FROM wr where morgue = '' order by siteName ASC"; 
		$fileName = "wrtwiki.txt";
		$query   = mysql_query($sql);
		if(mysql_affected_rows() > 0){
			
			$twikicode[] ='| *Count* | *Site* | *In* | *Out* | *Total Week* | *Exit Code (SAM)* | *Exit Code (HC)* | *Links* | *Ticket Number* | *No reply* |';
			$count = 0;
			
			while($veri = mysql_fetch_array($query))
				{
					$count++;
					$twikicode[] = '| '.$count.' | '.$veri[1].' | '.$operation->datecompare($veri[2]).' | '.''.' | '.$operation->calculateTotalWeek($veri[1] , $veri[2]).' | '.$operation->calculateFailTest("sam" , $veri[0] , "on").' | '.$operation->calculateFailTest("hc" , $veri[0] , "on").' | '.$operation->calculateFailTest("links" , $veri[0] , "on").' | '.'[['.$veri[5].']['.$veri[4].']] |' . ' |';     
				 }
				
			$fh = fopen("wrtwiki.txt", 'w') or die("can't open file");
			
			foreach ($twikicode as $twikiLine) 
				{
					$value = $twikiLine . "\n";
					fwrite($fh, $value);
				}
			fclose($fh);
		}
		
		$array["ok"] = "ok";
		echo json_encode($array);

		}

/***********************************NOTIFICATIONS*******************************************************/

	if($operations == 'notification-readStatus'){

		$id = $_POST['id'];
		$query = mysql_query("UPDATE notification SET readStatus = 'True' where id = $id");
		
		if($query){
			$array['ok'] = "ok";
		}else{
			$array['errors'] = "Error";
		}
		echo json_encode($array);
		
	}


/********************************************************************************************************/	


			if($operations == 'save')
				{
					$siteName = $_POST['siteName'];
					$date = $_POST['date'];
					$ticketNumber = $_POST['ticketNumber'];
					$ticketUrl = $_POST['ticketUrl'];
					$operation = new calculate();
					/****************************************************************************************/
					if(!$siteName || !$date || !$ticketNumber || !$ticketUrl)
						{
							$array['errors'] = 'Some errors occured.'; 
							echo json_encode($array);
						}
					elseif ($operation->checkdb($siteName) == 'duplicate')
						{
							$array['errors'] = 'This Site is already in WR.';
							echo json_encode($array);
						}
					else
						{
							/***If Everything is fine about fields , start the add to dataBase.**/
							$insert = mysql_query("INSERT INTO wr SET
							siteName = '$siteName',
							inDate 	 = '$date',
							ticketNumber = '$ticketNumber',
							ticketUrl = '$ticketUrl',
							wrinout   = 'x'
							");
					
							if(!$insert)
								{
									$array['errors'] = 'Some errors occured.';
									echo json_encode($array);
								}
							else 
								{

									$myid = mysql_insert_id();
									$array['id'] = $myid;							
									$array['ok'] = 'Record was appended successfully';	
									echo json_encode($array);
								}
								
						}
						
				}
/*******************************************************************************************************************************************************************************************************************************************************************************************************/

//*************************************************set morgue**********************************************************/

			if($operations == 'sendmorgue')
				{
					$id = $_POST['idWR'];
					// process of transfer into wrList table which is necessary for statistics
					$query = mysql_query("UPDATE wr SET morgue = 'x' where wrid = '$id'");
					//******************************************************************************
					if(!$query)
							{
								$array['errors'] = 'Some errors occured.';
							}
						else 
							{
								$array['ok'] = 'Record was saved successfully';	
							}
					echo json_encode($array);
				}
				
			if($operations == 'removemorgue')
				{
					$id = $_POST['idWR'];
					// process of transfer into wrList table which is necessary for statistics
					$query = mysql_query("UPDATE wr SET morgue = '' where wrid = '$id'");
					//******************************************************************************
					if(!$query)
							{
								$array['errors'] = 'Some errors occured.';
							}
						else 
							{

								$array['ok'] = 'Record was saved successfully';	
							}
					echo json_encode($array);
				}
				
				


//***************************************************************************************************************************************/


/*******************************************************************************************************************************************************************************************************************************************************************************************************/
			if($operations == 'remove')
				{
					$id = $_POST['idWR'];
					// process of transfer into wrList table which is necessary for statistics

					$query = mysql_query("SELECT * FROM wr where wrid = '$id'");
					while($data = mysql_fetch_row($query))
						{
							$siteName = $data[1];
							$inDate   = $data[2];
							$ticketNumber = $data[4];
							$ticketUrl = $data[5];
						};

					$outDate = date('Y-m-d');
					$start = strtotime($inDate);
					$end =   strtotime($outDate);
					$days_between = ceil((abs($end - $start) / 86400) / 7);
					$append = mysql_query("INSERT INTO wrList SET
					siteName  = '$siteName',
					inDate    = '$inDate',
					outDate   = '$outDate',
					totalWeek =  '$days_between',
					ticketUrl = '$ticketUrl',
					ticketNumber = '$ticketNumber',
					wrid 		 = '$id'
					");

					//******************************************************************************

					$delete = mysql_query("DELETE from wr where wrid = '$id'");
					if(!$delete)
							{
								$array['errors'] = 'Some errors occured.';
							}
						else 
							{

								$array['ok'] = 'Record was removed successfully';	
							}
					echo json_encode($array);

				}

		if($operations == 'saveweekly') // We Have to save Records(All Exit codes) to DB for Statistics 
			{
				$query = mysql_query("SELECT * from wr order by siteName ASC");
				if($query)
					{
						while($dataWr = mysql_fetch_array($query))
							{
								$querySam = mysql_query("SELECT * from samfailing where idWr = '$dataWr[0]'");
							 	if($querySam) 
							 		{
										while ($dataSam = mysql_fetch_array($querySam))
											{
												$insertSam = mysql_query("INSERT INTO sta_samfailing_week  SET siteName = '$dataWr[1]', exitCode = '$dataSam[2]', weekDate = curdate(), morgue = '$dataWr[6]' ");
												if (!$insertSam) { $array['errors'] = "Some errors occured";}
												else {$array['ok'] = "Records was saved successfully";}
											}
							 		}
							}
							
							echo json_encode($array);
					}
						
					$query = mysql_query("SELECT * from wr order by siteName ASC");
					if($query)
						{
						while($dataWr = mysql_fetch_array($query))
								{
									$queryHc = mysql_query("SELECT * from hcfailing where idWr = '$dataWr[0]'");
								 	if($queryHc) 
								 		{
											while ($dataHc = mysql_fetch_array($queryHc))
												{
					$insertHc = mysql_query("INSERT INTO sta_hcfailing_week  SET siteName = '$dataWr[1]', exitCode = '$dataHc[2]', weekDate = curdate(), morgue = '$dataWr[6]' ");
													if (!$insertHc) { $array['errors'] = "Some errors occured";}
													else {$array['ok'] = "Records was saved successfully";}
												}
								 		}

								 }
							//echo json_encode($array);
						}				
				
				
				$query = mysql_query("SELECT * from wr order by siteName ASC");
					if($query)
						{
						while($dataWr = mysql_fetch_array($query))
								
								{
								 	$queryLinks = mysql_query("SELECT * from linksfailing where idWr = '$dataWr[0]'");
								 	if($queryLinks) 
								 		{
											while ($dataLinks = mysql_fetch_array($queryLinks))
												{
													$insertLinks = mysql_query("INSERT INTO sta_linksfailing_week  SET siteName = '$dataWr[1]', goodT2fT1 = '$dataLinks[2]', goodT2tT1 = '$dataLinks[3]', activeT2fT1 = '$dataLinks[4]', activeT2tT1 = '$dataLinks[5]', weekDate = curdate(), morgue = '$dataWr[6]' ");
													if (!$insertHc) { $array['errors'] = "Some errors occured";}
													else {$array['ok'] = "Records was saved successfully";}
												}
								 		}

									
								}	}

			
			} // end of saveweekly


}

/*******************************************************************************************************************************************************************************************************************************************************************************************************/


?>