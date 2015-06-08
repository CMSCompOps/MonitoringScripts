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
	
	include ("lib/bootstrap.class.php");
	bootstrap::getNavBar(false, 'wrlist', 'Morgue List Table / Create Twiki Code');
	bootstrap::getHeadLine('Create morgue twiki');
	error_reporting(E_ALL);
	ini_set('display_errors', 1);

	function metricParser($lines){
	    preg_match_all("/(.*?)\t(.*?)\t(.*?)\t(.*?)\t(.*?)\n/m", $lines, $matches);
	    $result = array();
	    for($i = 0; $i < count($matches[0]); $i++){
	            $result[] = array('date' => $matches[1][$i], 'site' => $matches[2][$i],
	                              'value'=> $matches[3][$i], 'color'=> $matches[4][$i],
	                              'url'  => $matches[5][$i]);
	    }
	    return $result;
	}
	
	$sites = file_get_contents('https://jartieda.web.cern.ch/jartieda/Pledges_View_SSB/real.txt');
	$sites = metricParser($sites);
	
	function getRealCore($siteName, $sites){
	    foreach($sites as $site) if($site['site'] == $siteName) return $site['value'];
	    return null;
	}		
	
	
?>

<!--*********************************************************************************************-->	
	<div class="container">
		<?php
			$operation = new calculate();
			$query = mysql_query("SELECT * FROM wr where morgue = 'x' order by siteName ASC");
			if(mysql_affected_rows() <= 0){
			echo '<div class="alert alert-warning">WaitingRoom is empty Now.</div>';
			}else{ 

			$twikicode = '';
			echo '<div class="table-responsive">
			  <table class="table">
			  	<tr>
			  		<th> Count </th>
			  		<th> Site </th>
			  		<th> In </th>
			  		<th> Out </th>
			  		<th> Total Week </th>
			  		<th> Exit Code (SAM) </th>
			  		<th> Exit Code (HC) </th>
			  		<th> Links </th>
			  		<th> Real[cores] </th>
			  		<th> Ticket Number </th>
			  	</tr>';

			$twikicode[] ='| *Count* | *Site* | *In* | *Out* | *Total Week* | *Exit Code (SAM)* | *Exit Code (HC)* | *Links* | *Real[Cores]* | *Ticket Number* | *No reply* |';
			$count = 0;
			while($veri = mysql_fetch_array($query))
				{
					$count++;
					echo '<tr>';
					echo '<td>'.$count.'</td>';
					echo '<td>'.$veri[1].'</td>';
					echo '<td>'.$operation->morgueInOut($veri[2]).'</td>'; # in / out
					echo '<td></td>';
					echo '<td>'.$operation->calculateTotalWeek($veri[1] , $veri[2]).'</td>';
					echo '<td>'.$operation->calculateFailTest("sam" , $veri[0] , "off").'</td>';
					echo '<td>'.$operation->calculateFailTest("hc" , $veri[0] , "off").'</td>';
					echo '<td class = "links">'.$operation->calculateFailTest("links" , $veri[0] , "off").'</td>';
					echo '<td>' . getRealCore($veri[1], $sites) . '</td>';
					echo '<td><a target = "new" href = "' . $veri[5] . '">' . $veri[4] .  '</a></td>';
					echo '</tr>';
					$twikicode[] = '| '.$count.' | '.$veri[1].' | '.$operation->morgueInOut($veri[2]).' | '.''.' | '.$operation->calculateTotalWeek($veri[1] , $veri[2]).' | '.$operation->calculateFailTest("sam" , $veri[0] , "on").' | '.$operation->calculateFailTest("hc" , $veri[0] , "on").' | '.$operation->calculateFailTest("links" , $veri[0] , "on").' | ' . getRealCore($veri[1], $sites) . ' | ' .'[['.$veri[5].']['.$veri[4].']] |' . ' | ';     
				 }


			echo '</table></div>';

		?>
		<!-- Modal -->
		<div class="modal fade" id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
		  <div class="modal-dialog" style="width:600px;">
		    <div class="modal-content">
		      <div class="modal-header">
		        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
		        <h4 class="modal-title" id="myModalLabel">Copy Twiki Code into Your Twiki</h4>
		      </div>
		      <div class="modal-body">
				<div id="twikicoderesult"> <?php foreach ($twikicode as $value) {echo $value.'<br>';}?> </div>
		      </div>
		      <div class="modal-footer">
		        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
		        <button type="button" class="btn btn-success"   id="twikicodeSelect" >Select All</button>
		        <button type="button" class="btn btn-primary"   id="twikiFileMorgue" >Create File</button>
		      </div>
		    </div><!-- /.modal-content -->
		  </div><!-- /.modal-dialog -->
		</div><!-- /.modal -->


		<a class="btn btn-primary" id = "twikicodebtn" href="#" data-toggle="modal" data-target="#myModal" >Create twiki code</a>
<?php } ?>
	</div> <!--container divi-->

<!--**********************************************************************************************************-->
<?php bootstrap::getFooter(); ?>
<!--**********************************************************************************************************-->

<!--**********************************************************************************************************-->
  <script src="//code.jquery.com/jquery-1.9.1.js"></script>    
  <script src="//code.jquery.com/ui/1.10.4/jquery-ui.js"></script>
  	<script type="text/javascript" src = "js/moment.js"> </script>
  	<script type="text/javascript" src = "js/script.js"> </script>
	<script type="text/javascript" src="js/bootstrap.js"></script>	
	</body>
</html> 