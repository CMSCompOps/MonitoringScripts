<!DOCTYPE html>
<html>
	<head>
		<meta charset = "UTF-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0"> 
		<title></title>
		<link rel="shortcut icon" href="images/favicon.ico">		

		<link rel="stylesheet" href="images/style.css" type="text/css">
	    <script src="amcharts/amcharts.js" type="text/javascript"></script>
		<script src="amcharts/serial.js" type="text/javascript"></script>
		<script src="amcharts/radar.js" type="text/javascript"></script>
		<script src="amcharts/pie.js" type="text/javascript"></script>
		<link rel="stylesheet" type="text/css" href="css/bootstrap.css">
	    <link rel="stylesheet" href="//code.jquery.com/ui/1.10.4/themes/smoothness/jquery-ui.css"> 
	    <link rel="stylesheet" type="text/css" href="css/style.css"> 
		
		 <!-- scripts for exporting chart as an image -->
        <!-- Exporting to image works on all modern browsers except IE9 (IE10 works fine) -->
        <!-- Note, the exporting will work only if you view the file from web server -->
        <!--[if (!IE) | (gte IE 10)]> -->
        <script src="amcharts/exporting/amexport.js" type="text/javascript"></script>
        <script src="amcharts/exporting/rgbcolor.js" type="text/javascript"></script>
        <script src="amcharts/exporting/canvg.js" type="text/javascript"></script>
        <script src="amcharts/exporting/jspdf.js" type="text/javascript"></script>
        <script src="amcharts/exporting/filesaver.js" type="text/javascript"></script>
        <script src="amcharts/exporting/jspdf.plugin.addimage.js" type="text/javascript"></script>
        <!-- <![endif]-->

		
		  <!-- custom functions for Chart -->
		  <script type="text/javascript">
			AmCharts.loadJSON = function(url) 
				{
					// create the request
				  if (window.XMLHttpRequest) {
				    var request = new XMLHttpRequest();
				  } else {
				    var request = new ActiveXObject('Microsoft.XMLHTTP');
				  }
				  request.open('GET', url, false);
				  request.send();
				  return eval(request.responseText);
				};
		  </script>

  <script src="//code.jquery.com/jquery-1.9.1.js"></script>    
  <script src="//code.jquery.com/ui/1.10.4/jquery-ui.js"></script>
  <script type="text/javascript" src = "js/moment.js"> </script>
  <script type="text/javascript" src = "js/script.js"> </script>
  <script type="text/javascript" src = "js/charts.js"> </script>
  	
<!----------------------------------------------------------------------------->
	</head>
	<body>
	
	<?php 
	
	include ("lib/bootstrap.class.php");
	bootstrap::getNavBar(true, 'siteop', 'Summary');
	bootstrap::getHeadLine('Summary');
	
?>
<!--*********************************************************************************************-->	
 	<div class="container">
	<?php 
		$get = new bootstrap();
//getRow($chartName, $headLine, $SubheadLine = null, $conditionButton = false, $summaryList = false, $chartTypeBtn = 'BPL', $chartRotateBtn = false, $chartDateBtn = false )

		$get->getRow("WRoom" , "WaitingRoom", '', false, true, '', false, true);
		$get->getRow("Drain" , "Drain List", '', false, true, '', false, true);
		$get->getRow("Readiness" , "Site Readiness", '', true, true, 'B|L', true, true);

	?>
	
		
	
	</div> <!--#container divi-->
<?php

$operation = new getData();
list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-6 day", time() - 86400)), date('Y-m-d'), 153, 'T1');
$jsonData = json_decode($result, true);

list($jsonCode, $jsonCodeAll) = $operation->getJSONtoData($jsonData, $startDate, $endDate, false, 'red', 0, '', 'morgue');
echo '<script> makeChart(' . $jsonCode . ' , "bar" , "true" , "Days",  "WRoomChart");</script>';
echo '<script type="text/javascript">$(function(){$.kayitlar(' . $jsonCode . ', "WRoom", "Days");});</script>';


list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-6 day", time() - 86400)), date('Y-m-d'),  158, 'T2');
$jsonData = json_decode($result, true);
list($jsonCode, $jsonCodeAll) = $operation->getJSONtoData($jsonData, $startDate, $endDate, false,  'yellow');
echo '<script> makeChart(' . $jsonCode . ' , "bar" , "true" , "Days", "DrainChart") </script>';
echo '<script type="text/javascript">$(function(){$.kayitlar(' . $jsonCode . ', "Drain", "Days");});</script>';


list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-6 day", time() - 86400)), date('Y-m-d'),  45 , 'T2');
$jsonData = json_decode($result, true);
$jsonCode = $operation->getJSONtoData($jsonData, $startDate, $endDate, true,  '', 0 , 'T2');
echo '<script> makeChart(' . $jsonCode . ' , "line" , "false" , "average", "ReadinessChart") </script>';
echo '<script type="text/javascript">$(function(){$.kayitlar(' . $jsonCode . ', "Readiness", "average");});</script>';


?>

<!--**********************************************************************************************************-->

<!--**********************************************************************************************************-->
<!-- Modal -->
<div class="modal fade bs-example-modal-sm"  id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-sm">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h4 class="modal-title" id="myModalLabel">Search</h4>
      </div>
      <div class="modal-body">
       <form class="form" role="form" id="queryForm">
			<div class="form-group" style="margin-right: 10px;">
				<label for="timePeriod" style="font-size:12px;">Time Period</label>
			    <select name="timePeriod" style="font-size:12px;" id="timePeriod" class="form-control">
			    	<option value="24h" >24 hours</option>
			    	<option value="48h" >48 hours</option>
			    	<option value="Lweek" selected>Last week</option>
			    	<option value="L2week" >Last 2 weeks</option>
			    	<option value="Lmonth" >Last month</option>
			    	<option value="L2months" >Last 2 months</option>
			    	<option value="L3months" >Last 3 months</option>
			    	<option value="custom" >Custom...</option>
				</select> 
			</div>
       
			<div class="form-group" id="startDateGroup">
				<label style="font-size:12px;" for="startDate">Start Date</label>
				<input type="text" id="startDate" name="startDate" required class="form-control">
				
			</div>
			<div class="form-group" id="endDateGroup">
				<label style="font-size:12px;" for="endDate">End Date</label>
				<input type="text" id="endDate" name="endDate" required class="form-control">
			</div>

			<div class="form-group" style="margin-right: 10px;">
				<label for="tier" style="font-size:12px;">Select Site</label>
			    <select name="tier" style="font-size:12px;" id="tier" class="form-control">
			    	<option value="all" >all</option>
			    	<option value="T0/1">T0/1</option>
			    	<option value="T2" >T2</option>
			    	<option value="T0/1/2" >T0/1/2</option>
				</select> 
			</div>
		</form> 
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
        <button type="button" class="btn btn-success" onclick="$.queryDB('WRoom','Drain','Readiness');" data-dismiss="modal" id = "queryDB" >Query Database</button>
      </div>
    </div><!-- /.modal-content -->
  </div><!-- /.modal-dialog -->
</div><!-- /.modal -->


<div id="yukleniyor"></div>
<!--**********************************************************************************************************-->
<?php bootstrap::getFooter(); ?>

<!--**********************************************************************************************************-->

	<script type="text/javascript" src="js/bootstrap.js"></script>	
	 <script type="text/javascript">
$(window).bind("load", function() {
    $('#yukleniyor').fadeOut(2000);
});	
	</script>
	
	
	


	</body>
</html> 