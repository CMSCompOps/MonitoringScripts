<!DOCTYPE html>
<html>
	<head>
		<meta charset = "UTF-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0"> 
		<link rel="shortcut icon" href="images/favicon.ico">		
		<title></title>
		<link rel="stylesheet" type="text/css" href="css/bootstrap.css">
		<link rel="stylesheet" type="text/css" href="css/style.css">
	</head>
	<body>
	
	<?php 
		include('lib/bootstrap.class.php');
		bootstrap::getNavBar(false, 'siteop', 'Savannah Tickets', true);
		bootstrap::getHeadLine('gLExec');
	?>

<!--*********************************************************************************************-->	
<div class="container">
		<?php
		
				include("GlexecFunctions.php");
				$countT1s = 0;
				$countT2s = 0;
				$countT1sProblem = 0;
				$countT2sProblem = 0;					
				$countNoError = 0;					
				$countTotalSite = 0;
				list($siteList, $countT1s, $countT2s) = getAllCE();
				list($glexecList, $countT1sProblem, $countT2sProblem) = getGLEXEC($siteList);

				$countNoError = ($countT1s - $countT1sProblem) + ($countT2s - $countT2sProblem); 
			   	echo '<div class = "ceSummary">';
		   		echo  '<span  class = "badge badge-summary">T1s failing = ' . $countT1sProblem . "/" . $countT1s . '</span>';
				echo  '<span  class = "badge badge-summary">T2s failing = ' . $countT2sProblem . "/" . $countT2s . '</span>';
				echo  '<span  class = "badge badge-summary badge-summary-green">Sites ok = ' . $countNoError . '</span>';
				echo  '<button class = "btn btn-info btn-sm" data-toggle="modal" data-target="#submitModal">Summary</button>';									
			   echo '</div>';
			   	$count = 0;
				$panelHeadClass = "";
				echo '<div class="panel-group" id="accordion">';
				$keys = array_keys($glexecList);
				foreach ($glexecList as $keySite => $valueSite) {
						$countCE = 0;
						foreach ($valueSite as $keyHost => $valueHost) {$countCE++;}
						$count++;
						echo '<div class="panel panel-default cePanel">
					    <div class="panel-heading">
					      <h5 class="panel-title">
						        <a data-toggle="collapse" data-parent="#accordion" href="#collapse' . $count . '">
						          <span class = "panel_head"></span>' . $keySite . '</a>
						          <span class = "panel_head_red pull-right">CEs failing [' . $countCE . '] &nbsp;&nbsp;</span>' . '</b></span>
					      </h5>
					    </div>

					    <div id="collapse' . $count .'" class="panel-collapse collapse">
					    	<div class="panel-body">';
							/*
							 *  *********** CE Buttons ************************ 
							 */ 
							echo '<div class="button-group">'; 
							foreach ($valueSite as $keyHost => $valueHost) {
							//$url = "http://grid-monitoring.cern.ch/myegi/sam-pi/metric_output_details/?vo_name=cms&metric_name=org.cms.glexec.WN-gLExec&service_hostname=" . (string)$keyHost . "&service_flavour=CREAM-CE&check_time=" . $valueHost; 
									echo  '<a class = "btn btn-danger btn-sm ceBtn" href="' . $valueHost . '" target = new>'.  (string)$keyHost . '</a>';
							}
							echo '</div>'; //button group div
						echo '</div></div> </div>';
						} 
		?>
		
		<span class = "pull-right" style = "font-size : 10px; margin-top: 5px; cursor:default;"><b>Last Update</b> [ <?php echo date('m/d/Y H:i:s'); ?> UTC ] </span>
		
	</div> <!--container divi-->
	
	<?php
		$count = 0;
		ksort($ceErrors);
		$keys = array_keys($ceErrors);
		foreach ($ceErrors as $keySite => $valueSite) {
				$count++;
				if ((int)$ceCount[$keySite] != 0 && (substr($keySite, 0, 2) != 'T0') && (substr($keySite, 0, 2) != 'T3')  ){
					if ((int)$ceCount[$keySite] != 0){
						echo $keySite . "<hr>";
						foreach ($valueSite as $keyHost => $valueHost) {
							
							$url = "http://grid-monitoring.cern.ch/myegi/sam-pi/metric_output_details/?vo_name=cms&metric_name=org.cms.glexec.WN-gLExec&service_hostname=" . (string)$keyHost . "&service_flavour=CREAM-CE&check_time=" . $valueHost; 
									echo  '<a href="' . $url . '" target = new>'.  (string)$keyHost . '</a><br>';
						}
						echo "<hr>";
					}
				} // if
		} // foreach
			
	
	?>
<!--**********************************************************************************************************-->
<!-- Modal  Summary-->
<div class="modal fade" id="submitModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-dialog-message">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h4 class="modal-title" id="submitModalLabel">Summary</h4>
      </div>
      <div class="modal-body" id="submitModalBody">
      	<div id="twikicoderesult">
        		<?php 
        			echo '&lt;h4&gt; gLExec Summary &lt;/h4&gt;' . "<br>";
        			echo '&lt;pre&gt;' . "<br>";
					echo "T1s  failing : " . $countT1sProblem . "/" . $countT1s . "<br>";
					echo "T2s  failing : " . $countT2sProblem . "/" . $countT2s . "<br>";
					echo "Sites ok : " . $countNoError . "<br>";
        			echo '&lt;/pre&gt;';
        		?>
        </div>
      </div>
      <div class="modal-footer">
		<button type="button" class="btn btn-success"   id="twikicodeSelect" >Select All</button>      	
        <button type="button" class="btn btn-primary" data-dismiss="modal">Close</button>
      </div>
    </div><!-- /.modal-content -->
  </div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!--**********************************************************************************************************-->

	<?php bootstrap::getFooter(); ?>

  	<script src="js/jquery-1.9.1.js"></script>   
  	<script src="js/jquery-ui.js"></script>
	<script type="text/javascript" src="js/bootstrap.js"></script>	

	</body>
</html> 