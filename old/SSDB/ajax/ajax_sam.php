<?php
require ("../data/connect.php");

	if($_POST)
		{
			$samexitcode = $_POST['samexitcode'];
			$idWR  = $_POST['idWR'];
			$operation = $_POST['operation'];

			if($operation == 'addsam')
				{
					if(!$samexitcode || !$idWR)
						{
							$array['errors'] = 'Some errors occured.Please fill in the all of fields.';
						}
					else
						{
							/***If Everything is fine about fiels , start the add to dataBase.**/
							$insert = mysql_query("INSERT INTO samfailing SET
								idWr = '$idWR',
								exitCode = '$samexitcode'
							");
							
							if(!$insert)
								{
									$array['errors'] = 'Some errors occured during Add process';
								}
							else 
								{
									$array['ok'] = 'Record was appended successfully';
									$array['idSAM'] = mysql_insert_id();	
								}
							
						}	
					echo json_encode($array);
//					echo $json->encode($array);
				}

			if($operation == 'remove')	
				{
					$idSAM = $_POST['idSAM'];
					$delete = mysql_query("DELETE FROM samfailing where idSAM = '$idSAM'");
					if(!$delete){
					$array['errors'] = mysql_error();	
					}
					exit();
				}  
		}
	
?>