<?php

include("./data/connect.php");
include("./lib/getData.class.php");
include("./lib/date.class.php");
$operation = new getData();

if ($_POST){
	$endDate   = $_POST['endDate'];
	$startDate = $_POST['startDate'];
	$metric    = $_POST['metric'];
	$colorName = $_POST['colorName'];
	$condition = $_POST['condition'];
	$tier = $_POST['tier'];

	list($result, $endDate, $startDate) = $operation->getJSON(-1 , true , $startDate , $endDate, $metric, $tier);
	$jsonData = json_decode($result, true);
	$jsonCode = $operation->getJSONtoData($jsonData, $startDate, $endDate, true, '', $condition, $tier);
	echo json_encode($jsonCode);	
	
}



?>