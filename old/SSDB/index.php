<!DOCTYPE html>
<html>
	<head>
		<meta charset = "UTF-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0"> 
		<link rel="shortcut icon" href="images/favicon.ico">		
		<title></title>

		<link rel="stylesheet" href="images/style.css" type="text/css">
	    <script src="amcharts/amcharts.js" type="text/javascript"></script>
		<script src="amcharts/serial.js" type="text/javascript"></script>
		<script src="amcharts/radar.js" type="text/javascript"></script>
		<script src="amcharts/pie.js" type="text/javascript"></script>
		<link rel="stylesheet" type="text/css" href="css/bootstrap.css">
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

  <script type="text/javascript" src = "js/charts.js"> </script>
<!----------------------------------------------------------------------------->
	</head>
	<body>
		
	<?php 
	
	include ("lib/bootstrap.class.php");

	bootstrap::getNavBar(false, 'home', 'Site Support dataBase');
	$operate = new calculate();
	
?>


<!--*********************************************************************************************-->	
	<div class="container">
		<div class="row">
			<div class="col-md-6">
				<h5> <span style="margin-left:15px;"><b>Status WaitingRoom for this week</b></span></h5>
				<div id="Sum1" style="width: 100%; height:400px; "> </div>
			</div>

			<div class ="col-md-6">
				<h5> <span style="margin-left:15px;"><b>Drain List for week</b></span></h5>
				<div id="drainList" style="width: 100%; height:400px; "> </div>
				
			</div>
		</div> <!--#row div-->
		<div class="row">
			<div class = "container">
			<div class = "col-md-4">
				<div class="panel panel-default">
					<div class="panel-heading">
						<h3 class="panel-title">Sites In or Out for this week</h3>
					</div>
					<div class="panel-body panel-morgueinout">
					<?php
						$query = mysql_query("SELECT siteName, wrid, inDate, ticketUrl, ticketNumber FROM wr order by siteName ASC");
							while($veri = mysql_fetch_array($query))
								{
										$siteName[] = $veri['siteName'];
										$idWr[] 	= $veri['wrid'];
										$inDate[]   = $veri['inDate'];
										$ticketUrl[]  = $veri['ticketUrl'];
										$ticketNumber[] = $veri['ticketNumber']; 
								};
								$count = count($siteName) -1;
								$countItem = 0;
							?>
							<div class="list-group InOutWrList" id="siteInOut">
								<?php
									for($i=0; $i<=$count; $i++)
										{
											if($operate->datecompare($inDate[$i]) == 'x'){
												$countItem++;
												echo '<a  class="list-group-item list-group-item-danger" target = "new" href = "' . $ticketUrl[$i] . '">' 
												. $siteName[$i]
												. '<span class="pull-right  insite">'
												. '<span class = "siteOutRow">Tic.No: [' . $ticketNumber[$i] . ']</span>'
												. ' In </span>'
												. '</a>';
											}
										}
									if($countItem <= 0){
										echo '<div class="alert alert-warning alert-in">There is no any Sites In.</div>';									}	
										
							unset($query);
							unset($veri);
							
							
							
							$query = mysql_query("select siteName, outDate, ticketNumber, ticketUrl  from wrlist where (DATEDIFF(curdate(),outDate) < 3) group by siteName order by outDate Desc");
					   	 	if(mysql_affected_rows() > 0){
						   	 	while ($veri = mysql_fetch_array($query)) 
									{
											echo '<a  class="list-group-item waitingRoomListItems list-group-item-success" target = "new" href = "' . $veri['ticketUrl'] . '">'
											. $veri['siteName']
											. '<span class="pull-right  outsite">'
											. '<span class = "siteOutRow">Tic.No: [' . $veri['ticketNumber'] . ']</span>'
											. 'Out</span>'
											. '</a>';
									};
							}else{
									echo '<div class="alert alert-warning alert-out">There is no any Sites Out.</div>';				
							}
							?>
							
							</div><!--list-group-->
					</div>
				</div> <!-- panel -->
			</div> <!-- col-md-6 -->
			<div class = "col-md-4">
				<div class="panel panel-default">
					<div class="panel-heading">
						<h3 class="panel-title">Sites In Morgue for this week</h3>
					</div>
					<div class="panel-body panel-morgueinout">

					<?php
						unset($siteName);
						unset($query);
						unset($ticketNumber);
						unset($ticketUrl);
						$query = mysql_query("SELECT siteName, wrid,morgue, ticketNumber, ticketUrl FROM wr where morgue = 'x' order by siteName ASC");
						if(mysql_affected_rows() <= 0){
						echo '<div class="alert alert-warning">There is no any Sites In Morgue.</div>';
						}else{ 
						while($veri = mysql_fetch_array($query))
							{
									$siteName[] 	= $veri['siteName'];
									$ticketNumber[] = $veri['ticketNumber'];
									$ticketUrl[] 	= $veri['ticketUrl'];
							};
							$count = count($siteName) -1;
					?>
					<div class="list-group InOutWrList" id="sitesWR">
						<?php
							for($i=0; $i<=$count; $i++)
								{
									echo '<a  class="list-group-item waitingRoomListItems" target = "new" href = "' . $ticketUrl[$i] . '">' 
									. $siteName[$i]
									. '<span class = "pull-right outsite siteMorgueRow">Tic.No: [' . $ticketNumber[$i] . ']</span>'
									. '</a>';
								};
						?>
					</div>
				<?php } ?>
				</div> <!-- panel -->
			</div> <!-- col-md-6 -->
		</div>
			
			<div class="col-md-4">
				<div class="panel panel-default">
					<div class="panel-heading">
						<h3 class="panel-title"><font color = "#d73128">WaitingRoom Status <span class = "met153Head"> [metric 153 (without Morgue)]</span></font></h3>
					</div>
					<div class="panel-body panel-morgueinout">
					<?php
							#_______________________Eger WaitingRoom listesindeki site. Out Listesinde varsa onu almamasi icin listeyi al___________________ 
							unset($siteName);
							unset($query);
							$query = mysql_query("select siteName, outDate from wrlist where (DATEDIFF(curdate(),outDate) < 3) group by siteName order by outDate Desc");
							if($query){
								while($veri = mysql_fetch_array($query))
									{
											@$OutsiteName[] = $veri['siteName'];
									};
								}
							#_______________________________________________________________________________________________________________________________
					
						$operation = new getData();
						list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-0 day", time() - 86400)), date('Y-m-d'),  153, 'T1');
						$jsonData = json_decode($result, true);
						
						list($jsonCode, $jsonCodeAll) = $operation->getJSONtoData($jsonData, $startDate, $endDate, false, 'red', 0, '', 'morgue');
						
						
						$tmpJSON = json_decode($jsonCode, true);     
						foreach($tmpJSON as $key => $value){
							if (@!(in_array($tmpJSON[$key]['siteName'], @$OutsiteName))){
								echo '<a class = "list-group-item waitingRooListItems" target = "new" href ="https://dashb-ssb.cern.ch/dashboard/request.py/sitehistory?site='
								. $tmpJSON[$key]['siteName'] . '#currentView=Site+Readiness">'
								. $tmpJSON[$key]['siteName']
								. '<span class = "pull-right outsite siteMorgueRow"> Click to SSB</span>' . 
								
								"</a>";
							}
						}
					?>
					</div>
				</div> <!-- panel default -->
			</div> <!--col-md-4 wr read from metric 153 -->
			</div>
		</div> <!-- row -->
		
		<div class="row">
		<div class = "col-md-12">
				<h5> <span style="margin-left:15px;"><b>Site Readiness for this week</b></span></h5>
				<div id="siteReadiness" style="width: 100%; height:400px; "> </div>
		</div>
		</div> <!-- row -- >
		
		
	</div> <!--#container divi-->
<?php

list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-6 day", time() - 86400)), date('Y-m-d'),  153, 'T1');
$jsonData = json_decode($result, true);
list($jsonCode, $jsonCodeAll) = $operation->getJSONtoData($jsonData, $startDate, $endDate, false, 'red', 0, '', 'morgue');
echo '<script> makeChart(' . $jsonCode . ' , "bar" , "true" , "Days", "Sum1") </script>';

list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-6 day", time() - 86400)), date('Y-m-d'),  158, 'T2');
$jsonData = json_decode($result, true);
list($jsonCode, $jsonCodeAll) = $operation->getJSONtoData($jsonData, $startDate, $endDate, false,  'yellow');
echo '<script> makeChart(' . $jsonCode . ' , "bar" , "true" , "Days", "drainList") </script>';

list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-6 day", time() - 86400)), date('Y-m-d'),  45 , 'T2');
$jsonData = json_decode($result, true);
$jsonCode = $operation->getJSONtoData($jsonData, $startDate, $endDate, true,  '', 0 , 'T2');
echo '<script> makeChart(' . $jsonCode . ' , "line" , "false" , "average", "siteReadiness") </script>';
	
	?>
<!--**********************************************************************************************************-->
<?php bootstrap::getFooter(); ?>
<!--**********************************************************************************************************-->
    <script src="//code.jquery.com/jquery-1.9.1.js"></script>    
    <script src="//code.jquery.com/ui/1.10.4/jquery-ui.js"></script>
	<script type="text/javascript" src="js/bootstrap.js"></script>	
  	<script type="text/javascript" src = "js/moment.js"> </script>	
	<script type="text/javascript" src="js/script.js"> </script>
	 <script type="text/javascript">
$(window).bind("load", function() {
    $('#yukleniyor').fadeOut(2000);
});	
	</script>
	
	
	

	</body>
</html> 