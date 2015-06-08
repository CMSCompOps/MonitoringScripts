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
	bootstrap::getNavBar(false, 'wrlist', 'Morgue List');
	bootstrap::getHeadLine('Morgue Table');
	
?>

<!--*********************************************************************************************-->	
	<div class="container">
		<?php
			$operation = new calculate();
			$query = mysql_query("SELECT siteName,wrid,ticketNumber,ticketUrl,inDate,morgue FROM wr where morgue = 'x' order by siteName ASC");
			
			if(mysql_affected_rows() <= 0){
			echo '<div class="alert alert-warning">Morgue is empty Now.</div>';
			}else{ 
			
			while($veri = mysql_fetch_array($query))
				{
						$siteName[] = $veri['siteName'];
						$idWr[] 	= $veri['wrid'];
						$ticketNumber[] = $veri['ticketNumber'];
						$ticketUrl[]    = $veri['ticketUrl'];
						$inDate[]		= $veri['inDate'];
						$morgue[]       = $veri['morgue']; 
				};
				$count = count($siteName) -1;
				echo '<div class="panel-group" id="accordion">';
			for($i=0; $i<=$count; $i++)
				{ 
					
					echo '<div class="panel panel-default" id = wrPanel' . $idWr[$i] . '>
					    <div class="panel-heading">
					      <h4 class="panel-title">
					        <a data-toggle="collapse" class = "panelID" id="' . $idWr[$i] . '" data-parent="#accordion" href="#collapse'.$idWr[$i].'">
					          '. '<span class="panel_head">#SiteID: ' . $idWr[$i] . ' : </span>' . $siteName[$i].'</a>
					      </h4>
					    </div>
					    <div id="collapse'.$idWr[$i].'" class="panel-collapse collapse">
					    	<div class="panel-body">';?>

								<div class="panel panel-default wrListDetailPanel">
								  <div class="panel-heading">
								    <h3 class="panel-title">Site Details</h3>
								  </div>
								  <div class="panel-body">
								   
								  	<div class="container">
								  		<div class="row">
								  			<div class="col-md-4">
								  				<h5> <span><b>id : </b></span><span> <?php echo $idWr[$i]; ?> </span> </h5>
												<h5> <span><b>Indate : </b></span><span> <?php echo $inDate[$i]; ?>  </span> </h5>
												<h5> <span><b>Status Morgue  : </b></span><span> <?php echo ($morgue[$i] == 'x') ? "In" : "Out"; ?>  </span> </h5>

								  			</div>
								  			<div class="col-md-5">
												<h5> <span><b>Total Week  : </b></span><span> <?php echo $operation->calculateTotalWeek('', $inDate[$i]) . " week(s)"; ?>  </span> </h5>
								  				<h5> <span><b>Ticket Number : </b></span><span><a target = "new" href="<?php echo $ticketUrl[$i]; ?>"><?php echo $ticketNumber[$i]; ?> </a></span> </h5>
								  			</div>
								  			<div class="col-md-2">
												<button class = "btn btn-danger btn-sm" class="sendMorgue" data-toggle="modal" 															data-target="#myModalMorg">Get Out of <b>Morgue</b></button>
								  			</div>
								  		</div>
								  	</div>


								  </div>
								</div>
								<br>

								<ul class="nav nav-tabs" id="myTab">
								  <li class="active"><a href="#home<?php echo $idWr[$i]; ?>" data-toggle="tab">HC</a></li>
								  <li><a href="#profile<?php echo $idWr[$i]; ?>" data-toggle="tab">SAM</a></li>
								  <li><a href="#messages<?php echo $idWr[$i]; ?>" data-toggle="tab">Links</a></li>
								</ul>

								<div class="tab-content">
									<div class="tab-pane fade in active" id="home<?php echo $idWr[$i]; ?>">

										<div class="table-responsive errorList">
										  	<table class="table table-hover hcList" id="hcList">
											  	<tr>
												    <th>id</th>
												    <th>Exit Code</th>
												    <th>Operation</th>
												</tr>
												<?php
												$query = mysql_query("SELECT * FROM hcfailing where idWr = '$idWr[$i]' order by idHC ASC");

												echo '<div class="panel-group" id="accordion">';
												while($data = mysql_fetch_row($query))
													{   
														echo '<tr>';
														echo '<td>'.$data[0].'</td>';
														echo '<td class="hcexitcode">'.$data[2].'</td>';
														echo '<td> <a class="btn btn-danger btn-xs hcremoveExitCode"> Remove </a></td></tr>';
													}

												?>
										 	</table>
										</div><!--table-responsive-->
								  	</div>

								  <div class="tab-pane fade" id="profile<?php echo $idWr[$i]; ?>">
										<div class="table-responsive errorList">
										  	<table class="table table-hover samList" id="hcList">
											  	<tr>
												    <th>id</th>
												    <th>Exit Code</th>
												    <th>Operation</th>
												</tr>
												<?php
												$query = mysql_query("SELECT * FROM samfailing where idWr = '$idWr[$i]' order by idSAM ASC");

												echo '<div class="panel-group" id="accordion">';
												while($data = mysql_fetch_row($query))
													{   
														echo '<tr>';
														echo '<td>'.$data[0].'</td>';
														echo '<td class="samexitcode">'.$data[2].'</td>';
														echo '<td> <a class="btn btn-danger btn-xs samremoveExitCode"> Remove </a></td></tr>';
													}

												?>
										 	</table>
										</div><!--table-responsive-->
								  </div>

								  <div class="tab-pane fade" id="messages<?php echo $idWr[$i]; ?>">
										<div class="table-responsive errorList">
										  	<table class="table table-hover linksList" id="hcList">
											  	<tr>
												    <th>id</th>
												    <th>Good<br>T2 from T1</th>
												    <th>Good<br>T2 to T1</th>
												    <th>Active<br>T2 from T1</th>
												    <th>Active<br>T2 to T1</th>
												    <th>Operation</th>
												</tr>

												<?php
												$query = mysql_query("SELECT * FROM linksfailing where idWr = '$idWr[$i]' order by idLINKS ASC");

												echo '<div class="panel-group" id="accordion">';
												while($data = mysql_fetch_row($query))
													{   
														echo '<tr>';
														echo '<td>'.$data[0].'</td>';
														echo '<td>'.$data[2].'</td>';
														echo '<td>'.$data[3].'</td>';
														echo '<td>'.$data[4].'</td>';
														echo '<td>'.$data[5].'</td>';
														echo '<td><a class="btn btn-danger btn-xs linksremoveExitCode"> Remove </a></td></tr>';
													}

												?>
										 	</table>
										</div><!--table-responsive-->
								  </div>
								</div>
					
<?php echo '</div></div> </div>'; // respectively -> these are a end of [panel-body, panel-collapse, panel-default] divs
					  
				}; 
		?>
		<span id = "siteID" style="display:none"> </span>
		<?php } ?>
				<a class="btn btn-primary btn-sm" style="margin-top:10px;" href="morgue_table.php" >Create Morgue Table</a>

	</div> <!--container divi-->
<!--**********************************************************************************************************-->
<!--**********************************************************************************************************-->
<!-- Modal -->
<div class="modal fade" id="myModalwR" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h4 class="modal-title" id="myModalLabel">Remove Site from WaitingRoom</h4>
      </div>
      <div class="modal-body">
        Do you want to get this site out of WaitingRoom? 
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
        <button type="button" class="btn btn-danger" data-dismiss="modal" id = "getOutWr" >Remove Site</button>
      </div>
    </div><!-- /.modal-content -->
  </div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!--**********************************************************************************************************-->


<!--**********************************************************************************************************-->
<!-- Modal -->
<div class="modal fade" id="myModalMorg" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h4 class="modal-title" id="myModalLabel">Remove Site from Morgue</h4>
      </div>
      <div class="modal-body">
      	This site will be back to <span> <b><font color="#d53026">WaitingRoom.</font></b> </span> Do you want to get this site out of Morgue?
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
        <button type="button" class="btn btn-danger" data-dismiss="modal" id = "removeMorgue" >Remove Site</button>
      </div>
    </div><!-- /.modal-content -->
  </div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!--**********************************************************************************************************-->



	<?php bootstrap::getFooter(); ?>

<!--**********************************************************************************************************-->

  	<script src="//code.jquery.com/jquery-1.9.1.js"></script>    
  	<script src="//code.jquery.com/ui/1.10.4/jquery-ui.js"></script>
  	<script type="text/javascript" src = "js/moment.js"> </script>
  	<script type="text/javascript" src = "js/script.js"> </script>
	<script type="text/javascript" src="js/bootstrap.js"></script>	

	</body>
</html> 