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
			/*
			 *********************Read XML on ssb ***************************************
			 */ 
				function getXMLfromURL($url){
					$curl = curl_init();
					curl_setopt($curl, CURLOPT_URL , $url);
					curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
					$xml = curl_exec($curl);
					curl_close($curl);
					return $xml;
				}
				/*
				 *  ***************************** To get Warning *****************************************************
				 */
					$data =  getXMLfromURL("http://grid-monitoring.cern.ch/myegi/sam-pi/latest_metric_results_in_profile/?vo_name=cms&profile_name=CMS_CRITICAL_FULL&service_hostname=&service_flavour=CREAM-CE");
					$xml = simplexml_load_string($data);
					$countT1s = 0;
					$countT2s = 0;
					$countT1sProblem = 0;
					$countT2sProblem = 0;					
					$countNoError = 0;					
					$countTotalSite = 0;
					foreach($xml->Profile->Group as $site){
						$countTotalSite++;
						$siteName = (string)$site["name"];
						$ceCount[$siteName] = array();
						$ceErrors[$siteName] = array();
						$tmpCeCount = 0;
						if ($site->Service){
							$countService = count($site->Service);
							for ($j=0; $j < $countService; $j++) { 
								if($site->Service[$j]->Metric){
									$countMtr = count($site->Service[$j]->Metric);
									$hostName = (string)$site->Service[$j]['hostname'];
									for ($i=1; $i < $countMtr; $i++) {
									  	if($site->Service[$j]->Metric[$i]['name'] == 'org.cms.glexec.WN-gLExec' && $site->Service[$j]->Metric[$i]['status'] != 'OK'){
									  		/** bu bolgede sorgulama yapilacak diger linke **/
									  	    $exec_time = (string)$site->Service[$j]->Metric[$i]['exec_time'];
									  	    $message = getXMLfromURL("http://grid-monitoring.cern.ch/myegi/sam-pi/metric_output_details/?vo_name=cms&metric_name=org.cms.glexec.WN-gLExec&service_hostname=" . $hostName . "&service_flavour=CREAM-CE&check_time=" . $exec_time);
									  		if(strpos($message, "Warning: Same /usr/bin/id for payload and pilot") == false){
												$ceErrors[$siteName][$hostName] =  $exec_time;
												$tmpCeCount++;
									  		}
									  	} // if site->Services->Metric = org.cms.glexec.WN-gLExec
									} // for countMtr
								} // if site->Services->Metric
							} // for services 
						} // for countServices
						$ceCount[$siteName] = $tmpCeCount;
						$tierName = substr($siteName, 0,2);
						if ($tierName == 'T1'){$countT1s++;}
						if ($tierName == 'T2'){$countT2s++;}
						if ($tmpCeCount != 0){
							if ($tierName == 'T1'){$countT1sProblem++;}
							if ($tierName == 'T2'){$countT2sProblem++;}
						} 	 
					} // site foreach
			 /*
			  ************************************************************************************
			  */
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
				ksort($ceErrors);
				$keys = array_keys($ceErrors);
				foreach ($ceErrors as $keySite => $valueSite) {
						$count++;
						if ((int)$ceCount[$keySite] == 0){$panelHeadClass = "panel_head_green";} else {$panelHeadClass = "panel_head_red";}
						if ((int)$ceCount[$keySite] != 0 && (substr($keySite, 0, 2) != 'T0') && (substr($keySite, 0, 2) != 'T3')  ){ 
						echo '<div class="panel panel-default cePanel">
					    <div class="panel-heading">
					    
					      <h5 class="panel-title">
						        <a data-toggle="collapse" data-parent="#accordion" href="#collapse' . $count . '">
						          <span class = "panel_head"></span>' . $keySite . '</a>
						          <span class = "' . $panelHeadClass . ' pull-right">CEs failing [' . $ceCount[$keySite] . '] &nbsp;&nbsp;</span>' . '</b></span>
					      </h5>
					    </div>

					    <div id="collapse' . $count .'" class="panel-collapse collapse">
					    	<div class="panel-body">';
							/*
							 *  *********** CE Buttons ************************ 
							 */ 
						 	if ((int)$ceCount[$keySite] != 0){
							echo '<div class="button-group">'; 
							foreach ($valueSite as $keyHost => $valueHost) {
							$url = "http://grid-monitoring.cern.ch/myegi/sam-pi/metric_output_details/?vo_name=cms&metric_name=org.cms.glexec.WN-gLExec&service_hostname=" . (string)$keyHost . "&service_flavour=CREAM-CE&check_time=" . $valueHost; 
									echo  '<a class = "btn btn-danger btn-sm ceBtn" href="' . $url . '" target = new>'.  (string)$keyHost . '</a>';
							}
							echo '</div>'; //button group div
							}else{
								echo '<div class="alert alert-success alert-in">There is no errors.</div>';
							}						
						echo '</div></div> </div>';
						} }
		?>
		
	</div> <!--container div-->
		<span class = "pull-right" style = "font-size : 10px; margin-top: 5px; cursor:default;"><b>Last Update</b> [ <?php echo date('m/d/Y H:i:s'); ?> UTC ] </span>
		
	</div> <!--container div-->
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