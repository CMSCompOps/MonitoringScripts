<?php
require ("../data/connect.php");

	if($_POST)
		{
			/**************************Read data from form by Script*********************************/
			$goodT2fT1	 = $_POST['goodT2fT1'];
			$goodT2tT1	 = $_POST['goodT2tT1'];
			$activeT2fT1 = $_POST['activeT2fT1'];
			$activeT2tT1 = $_POST['activeT2tT1'];
			$idWR = $_POST['idWR'];
			$operation = $_POST['operation'];

			if($operation == 'addlinks')
				{
				//	if(!$goodT2fT1 || !$goodT2tT1 || !$activeT2fT1 || !$activeT2tT1 || !$idWR)
				//		{
				//			$array['errors'] = 'Some errors occured.Please fill in the all of fields.';
				//		}
				//	else
						{
							/***If Everything is fine about fiels , start the add to dataBase.**/
							$insert = mysql_query("INSERT INTO linksfailing SET
								idWr = '$idWR',
								goodT2fT1 	= '$goodT2fT1',
								goodT2tT1 	= '$goodT2tT1',
								activeT2fT1 = '$activeT2fT1',
								activeT2tT1 = '$activeT2tT1'
							");
							
							if(!$insert)
								{
									$array['errors'] = 'Some errors occured during Add process';
								}
							else 
								{
									$array['ok'] = 'Record was appended successfully';
									$array['idLINKS'] = mysql_insert_id();	
								}
							
						}	
					echo json_encode($array);
//					echo $json->encode($array);
					
				}
			/****************************************************************************************/

			if($operation == 'remove')
				{
					$idLINKS = $_POST['idLINKS'];
					$delete = mysql_query("DELETE FROM linksfailing where idLINKS = '$idLINKS'");
					if(!$delete){
					$array['errors'] = mysql_error();	
					}
					exit();
				}
		}

?>