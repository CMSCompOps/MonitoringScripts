<?php
	include("../data/connect.php");
	include("../lib/getData.class.php");
	include("../lib/date.class.php");
	$operation = new getData();

if ($_POST){
	
	$endDate   = $_POST['endDate'];
	$startDate = $_POST['startDate'];
	$metric    = $_POST['metric'];
	$colorName = $_POST['colorName'];
	$DB 	   = $_POST['DB'];
	$tier 	   = $_POST['tier'];

	if($DB){
		list($result, $endDate, $startDate) = $operation->getJSONfromDB(true , $startDate, $endDate, $DB);
		$jsonCode = json_decode($result, true);
		
	}else{
		list($result, $endDate, $startDate) = $operation->getJSON(-1 , true , $startDate , $endDate, $metric, $tier); // Tier Gelecek..
		$jsonData = json_decode($result, true); // buradaki code dan dolayi calismada problem cikiyor..
		if ($colorName != "sr") {
			list($jsonCode, $jsonCodeAll) = $operation->getJSONtoData($jsonData, $startDate, $endDate, false, $colorName, 0, $tier, '');
		}else{
			$jsonCode = $operation->getJSONtoData($jsonData, $startDate, $endDate, true, '', 0, $tier, '');
		}
	}
	echo json_encode($jsonCode);	

}

?>