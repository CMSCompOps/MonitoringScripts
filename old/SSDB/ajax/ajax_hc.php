<?php
require ("../data/connect.php");

	if($_POST)
		{
			/**************************Read data from form by Script*********************************/
			$hcExitCode = $_POST['hcexitcode'];
			$idWR = $_POST['idWR'];
			$operation = $_POST['operation'];
			if($operation == 'addhc')
				{
					if(!$hcExitCode || !$idWR)
						{
							$array['errors'] = 'Some errors occured.Please fill in the all of fields.';
						}
					else
						{
							/***If Everything is fine about fiels , start the add to dataBase.**/
							$insert = mysql_query("INSERT INTO hcFailing SET
								idWr = '$idWR',
								exitCode = '$hcExitCode'
							");
							
							if(!$insert)
								{
									$array['errors'] = 'Some errors occured during Add process';
								}
							else 
								{
									$array['ok'] = 'Record was appended successfully';
									$array['idHC'] = mysql_insert_id();	
								}
							
						}	
					echo json_encode($array);
//					echo $json->encode($array);
				}
			/****************************************************************************************/

			if($operation == 'remove')
				{
					$idHC = $_POST['idHC'];
					$delete = mysql_query("DELETE FROM hcfailing where idHC = '$idHC'");
					if(!$delete){
					$array['errors'] = mysql_error();	
					}
					exit();
				}
		}

?>