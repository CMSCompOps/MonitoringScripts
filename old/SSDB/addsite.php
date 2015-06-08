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
	bootstrap::getNavBar(false, 'wrlist', 'Add / Remove a new Site');
	
?>
<!--*********************************************************************************************-->	
		<div class="container">
			<div class="row">
				<div class="col-md-6"><!--waitingroom site form-->
					<form role="form-horizontal" id="siteForm">
						<div class="form-group">
					    	<label for="siteName">Site Name</label>
					    	<select name="siteName" id="siteName" class="form-control"></select>
					  	</div>
					  	<div class="form-group">
					    	<label for="date">In Date</label>
						    <input type="date" id="date" name="date" required class="form-control">
						</div>
						<div class="form-group">
						    <label for="ticketNumber">Ticket Number</label>
						    <input type="text" class="form-control" id="ticketNumber" name="ticketNumber" placeholder="Ticket Number">
					  	</div>
					  	<div class="form-group">
						    <label for="ticketUrl">Ticket URL</label>
						    <input type="text" class="form-control" id="ticketUrl" name="ticketUrl" placeholder="Ticket URL">
					  	</div>
					  	<a onclick="$.save();" id="siteSaveBtn" class="btn btn-primary">Save This Site as "IN"</a>

					</form>
				</div><!--col-md-6-->
				<div class="col-md-6"><!--waitingroom list-->
					<h4>WaitingRoom List</h4>
					<?php
						include ("data/connect.php");
						$query = mysql_query("SELECT siteName,wrid,morgue FROM wr order by siteName ASC");
						while($veri = mysql_fetch_array($query))
							{
									$siteName[] = $veri['siteName'];
									$idWr[] 	= $veri['wrid'];
									$morgue[]   = $veri['morgue'];
							};
							$count = count($siteName) -1;
					?>
					<div class="list-group waitingRoomList" id="waitingRoomList">
						<?php
							for($i=0; $i<=$count; $i++)
								{
									echo '<a href="#"  class="list-group-item waitingRoomListItems">'
									.$siteName[$i]
									. '<span style="display:none;" class="waitingRoomListItem">' 
									.$idWr[$i] 
									. '</span>' 
									. '<span class= "pull-right"><button type="button" class="btn btn-danger btn-xs" data-toggle="modal" data-target="#myModal">Get Out of WaitingRoom</button></span>';
						
				  			 if($morgue[$i] == 'x'){
						  			echo
									 '<span class= "pull-right"><button type="button" disabled = "true" class="btn btn-danger btn-xs" data-toggle="modal" data-target="#myModalMorg" style="margin-right:5px;">Send to Morgue</button></span>'
									.'</a>';}
									else {
						  			echo
									 '<span class= "pull-right"><button type="button"  class="btn btn-danger btn-xs" data-toggle="modal" data-target="#myModalMorg" style="margin-right:5px;">Send to Morgue</button></span>'
									.'</a>';
									
									}
									
									
									
								};
							
						?>
					</div><!--list-group-->
				</div><!--col-md-6-->
				<div class="col-md-12 siteerror-panel" id="siteerror-panel"><!--site errors bolgesi-->
					<div class="panel panel-default">
						<div class="panel-heading">
					    	<h3 class="panel-title" id="siteErrorPanel">Site Errors</h3>
						</div><!--panel-heading-->
						<div class="panel-body">
							<ul class="nav nav-pills">
							  <li class="active"><a href="#hc" data-toggle="tab">HC</a></li>
							  <li><a href="#sam" data-toggle="tab">SAM</a></li>
							  <li><a href="#links" data-toggle="tab">Links</a></li>
							</ul><!--nav nav-pills-->
							<div class="tab-content">
								<div class="tab-pane fade in active" id="hc">
									<div class="row">
										<div class="col-md-6">
											<form role="form-horizontal" id="hcForm">
											  	<div class="form-group">
												    <label for="siteName">HC Exit Code</label>
												    <select name="hcexitcode" id="hcexitcode" class="form-control"></select>
											  	</div><!--form-group-->
										  		<a onclick="$.addHCExitCode();" class="btn btn-primary">Add Exit Code</a>
											</form><!--hc form-->
										</div><!--col-md-6-->

										<div class="col-md-6">
											<b>HC Error List</b>
											<div class="table-responsive errorList">
											  	<table class="table table-hover hcList" id="hcList">
												  	<tr>
													    <th>id</th>
													    <th>Exit Code</th>
													    <th>Operation</th>
													</tr>
											 	</table>
											</div><!--table-responsive-->
										</div><!--col-md-6-->
									</div>
								</div><!--tab-pane fade in active HC-->
								<div class="tab-pane fade" id="sam">
									<div class="row">
										<div class="col-md-6">
											<form role="form-horizontal" id="samForm">
											  	<div class="form-group">
												    <label for="siteName">SAM Exit Code</label>
												    <select name="samexitcode" id="samexitcode" class="form-control">
												    	<option value="n/a">n/a</option>
												    	<option value="all">all</option>
														<option value="0% - cream.CREAMCE">0% - cream.CREAMCE</option>
														<option value="emi.cream.CREAMCE-JobSubmit">emi.cream.CREAMCE-JobSubmit</option>
														<option value="org.cms.glexec.WN-gLExec">org.cms.glexec.WN-gLExec</option>
														<option value="org.cms.WN-analysis">org.cms.WN-analysis</option>
														<option value="org.cms.WN-basic">org.cms.WN-basic</option>
														<option value="org.cms.WN-env">org.cms.WN-env</option>
														<option value="org.cms.WN-frontier">org.cms.WN-frontier</option>
														<option value="org.cms.WN-mc">org.cms.WN-mc</option>
														<option value="org.cms.WN-squid">org.cms.WN-squid</option>
														<option value="org.cms.WN-swinst">org.cms.WN-swinst</option>
														<option value="org.cms.WN-xrootd-access">org.cms.WN-xrootd-access</option>
														<option value="org.cms.WN-xrootd-fallback">org.cms.WN-xrootd-fallback</option>
														<option value="org.cms.SRM-GetPFNFromTFC">org.cms.SRM-GetPFNFromTFC</option>
														<option value="org.cms.SRM-VOGet">org.cms.SRM-VOGet</option>
														<option value="org.cms.SRM-VOPut">org.cms.SRM-VOPut</option>
													</select>
											  	</div><!--form-group-->
										  		<a onclick="$.addSAMExitCode();" class="btn btn-primary">Add Exit Code</a>
											</form><!--hc form-->
										</div><!--col-md-6-->

										<div class="col-md-6">
											<b>SAM Error List</b>
											<div class="table-responsive errorList">
											  	<table class="table table-hover samList" id="samList">
												  	<tr>
													    <th>id</th>
													    <th>Exit Code</th>
													    <th>Operation</th>
													</tr>
											 	</table>
											</div><!--table-responsive-->
										</div><!--col-md-6-->
									</div>
								</div><!--tab-pane fade in active SAM-->
							  	<div class="tab-pane fade" id="links">
							  		<div class="row">
										<div class="col-md-6">
											<form role="form-horizontal" id="linksForm">
											  	<div class="form-group">
												    <label for="goodT2fT1">Good T2 links from T1s</label>
												    <select name="goodT2fT1" id="goodT2fT1" class="form-control col-xs-4"></select>
											  	</div><!--form-group-->
											  	<div class="form-group">
												    <label for="goodT2tT1">Good T2 links to T1s</label>
												    <select name="goodT2tT1" id="goodT2tT1" class="form-control col-xs-4"></select>
											  	</div><!--form-group-->
											  	<div class="form-group">
												    <label for="activeT2fT1">Active T2 links from T1s</label>
												    <input type="text" class="form-control" id="activeT2fT1" name="activeT2fT1" placeholder="Active T2 links from T1s">
											  	</div>

 												<div class="form-group">
												    <label for="activeT2tT1">Active T2 links to T1s</label>
												    <input type="text" class="form-control" id="activeT2tT1" name="activeT2tT1" placeholder="Active T2 links to T1s">
											  	</div>
												<a onclick="$.addLINKSExitCode();" class="btn btn-primary">Add Exit Code</a>
											</form><!--linka form-->

										</div><!--col-md-6-->

										<div class="col-md-6">
											<b>Links Error List</b>
											<div class="table-responsive errorList">
											  	<table class="table table-hover linksList" id="linksList">
												  	<tr>
													    <th>id</th>
													    <th>Good<br>T2 from T1</th>
													    <th>Good<br>T2 to T1</th>
													    <th>Active<br>T2 from T1</th>
													    <th>Active<br>T2 to T1</th>
													    <th>Operation</th>
													</tr>
											 	</table>
											</div><!--table-responsive-->
										</div><!--col-md-6-->
									</div>
							  	</div><!--tab-pane fade in active LINKS-->
							</div><!--tab-content-->
						</div><!--panel-body-->
					</div><!--panel panel-default-->
				</div><!--col-md-12-->
			</div><!--row-->
		</div> <!--container-->	
<!--**********************************************************************************************************-->
<div id="wrId" style="display:none;"></div><!--kayit yapilan Site'a ait id'nin saklandigi yer-->
<div id="waitingRoomListid" style="display:none;"></div><!--removesite yapabilmek icin tiklanan site in idsini sakladigimiz div-->

<div class="container">
	<div class="alert alert-danger"><b><span class="glyphicon glyphicon-remove"></span>Some errors occured.</b></div>
</div>
<!--**********************************************************************************************************-->

<!--**********************************************************************************************************-->
<!-- Modal -->
<div class="modal fade" id="myModal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
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
        <button type="button" class="btn btn-danger" data-dismiss="modal" id = "removeSite" >Remove Site</button>
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
        <h4 class="modal-title" id="myModalLabel">Send Site to Morgue</h4>
      </div>
      <div class="modal-body">
        Do you want to send this site to Morgue? 
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
        <button type="button" class="btn btn-danger" data-dismiss="modal" id = "sendMorguefromadd" >Send to Morgue</button>
      </div>
    </div><!-- /.modal-content -->
  </div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!--**********************************************************************************************************-->


<?php bootstrap::getFooter(); ?>
<!--**********************************************************************************************************-->
    <script src="//code.jquery.com/jquery-1.9.1.js"></script>    
    <script src="//code.jquery.com/ui/1.10.4/jquery-ui.js"></script>
	<script type="text/javascript" src="js/bootstrap.js"></script>	
	<script type="text/javascript" src = "js/moment.js"> </script>
	<script type="text/javascript" src="js/script.js"> </script>

	</body>
</html> 