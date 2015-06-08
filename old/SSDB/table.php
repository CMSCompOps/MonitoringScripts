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
	bootstrap::getNavBar(false, 'wrlist', 'WaitingRoom List Table / Create Twiki Code');
	bootstrap::getHeadLine('Create waiting room twiki');

	
?>

<!--*********************************************************************************************-->	
	<div class="container">
		<?php
			$operation = new calculate();
			$query = mysql_query("SELECT * FROM wr where morgue = '' order by siteName ASC");
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
			  		<th> Ticket Number </th>
			  	</tr>';

			$twikicode[] ='| *Count* | *Site* | *In* | *Out* | *Total Week* | *Exit Code (SAM)* | *Exit Code (HC)* | *Links* | *Ticket Number* | *No reply* |';
			$count = 0;
			while($veri = mysql_fetch_array($query))
				{
					$count++;
					echo '<tr>';
					echo '<td>'.$count.'</td>';
					echo '<td>'.$veri[1].'</td>';
					echo '<td>'.$operation->dateCompare($veri[2]).'</td>'; # in / out
					echo '<td></td>';
					echo '<td>'.$operation->calculateTotalWeek($veri[1] , $veri[2]).'</td>';
					echo '<td>'.$operation->calculateFailTest("sam" , $veri[0] , "off").'</td>';
					echo '<td>'.$operation->calculateFailTest("hc" , $veri[0] , "off").'</td>';
					echo '<td class = "links">'.$operation->calculateFailTest("links" , $veri[0] , "off").'</td>';
					echo '<td><a target = "new" href = "' . $veri[5] . '">' . $veri[4] .  '</a></td>';
					echo '</tr>';
					$twikicode[] = '| '.$count.' | '.$veri[1].' | '.$operation->datecompare($veri[2]).' | '.''.' | '.$operation->calculateTotalWeek($veri[1] , $veri[2]).' | '.$operation->calculateFailTest("sam" , $veri[0] , "on").' | '.$operation->calculateFailTest("hc" , $veri[0] , "on").' | '.$operation->calculateFailTest("links" , $veri[0] , "on").' | '.'[['.$veri[5].']['.$veri[4].']] |' . ' |';                
				 }

			$query = mysql_query("select siteName, outDate, ticketNumber, ticketURL from wrlist where (DATEDIFF(curdate(),outDate) < 3) group by siteName order by outDate Desc");
	   	 	while ($veri = mysql_fetch_array($query)) 
				{
					echo '<tr>';
					echo '<td></td>';
					echo '<td>'.$veri[0].'</td>';
					echo '<td></td>';
					echo '<td>'.'x'.'</td>';
					echo '<td></td>';
					echo '<td></td>';
					echo '<td></td>';
					echo '<td></td>';
					//echo '<td>' . $veri[2] . '</td>';
					echo '<td><a target = "new" href = "' . $veri[3] . '">' . $veri[2] .  '</a></td>';
					echo '</tr>';
					$twikicode[] = '|  | '.$veri[0].' |  | x |  |  |  |  | ' . '[['.$veri[3].']['.$veri[2].']] |' . '  |';
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
		        <button type="button" class="btn btn-primary"   id="twikiFileWr" >Create File</button>
		      </div>
		    </div><!-- /.modal-content -->
		  </div><!-- /.modal-dialog -->
		</div><!-- /.modal -->



		<!-- saveWeeklyModal -->
		<div class="modal fade" id="saveWeeklyModal" tabindex="-1" role="dialog" aria-labelledby="saveWeeklyModalLabel" aria-hidden="true">
		  <div class="modal-dialog">
		    <div class="modal-content">
		      <div class="modal-header">
		        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
		        <h4 class="modal-title" id="saveWeeklyModalLabel">Save WR Table into DataBase</h4>
		      </div>
		      <div class="modal-body"> Do you want to Save WR Table into DataBase?</div>
		      <div class="modal-footer">
		        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
		        <button type="button" class="btn btn-success" data-dismiss = "modal"  id="saveWeeklyBtn" >Save</button>
		      </div>
		    </div><!-- /.modal-content -->
		  </div><!-- /.modal-dialog -->
		</div><!-- /.saveWeeklyModal -->

		<a class="btn btn-primary" id = "twikicodebtn" href="#" data-toggle="modal" data-target="#myModal" >Create twiki code</a>
		<a class="btn btn-success" id = "saveweekly" href="#"  data-toggle="modal" data-target="#saveWeeklyModal">Save Weekly</a>
<?php } ?>
	</div> <!--container divi-->

<!--**********************************************************************************************************-->
<?php bootstrap::getFooter(); ?>
<!--**********************************************************************************************************-->

<!--**********************************************************************************************************-->
  <script src="//code.jquery.com/jquery-1.9.1.js"></script>    
  <script src="//code.jquery.com/ui/1.10.4/jquery-ui.js"></script>
  	<script type="text/javascript" src = "js/script.js"> </script>
	<script type="text/javascript" src = "js/moment.js"> </script>
	<script type="text/javascript" src="js/bootstrap.js"></script>	
	</body>
</html> 