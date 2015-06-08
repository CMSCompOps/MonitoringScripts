<?php
/*! 
 *  \details   Site Support DataBase Monitoring
 *  \author    Gökhan Kandemir
 *  \version   1.0
 *  \date      2014
 *  \copyright Site Support Team
 */
class bootstrap{

/* 		
 * ****************************** This function is used for creating menu - submenu *******************************************************************
 */
	function getNavBar($searchForm = false, $active = null, $brand = null, $disabled = false){
		include("data/connect.php"); // connect to mysql 
		include("getData.class.php"); // 
		include("date.class.php");
		include("notifications.class.php");
		$obj = new notifications();
		$obj->checkNotifications();
		$home = ''; $siteOperations = ''; $wrList = ''; ; $notif = '';
		if ($active == 'home')   {$home = 'active';};
		if ($active == 'siteop') {$siteOperations = 'active';};
		if ($active == 'wrlist') {$wrList = 'active';};
		if ($active == 'notif') {$notif  = 'active';};
		if ($disabled == false) {$disabled = '';} else {$disabled = 'disabled';};
		
		
		echo '
		<nav class="navbar navbar-inverse navbar-static-top" id = "sidebar">
			<div class="container">
				<span class="navbar-brand navbar-image brand_Headline">';
				if($disabled == 'disabled'){
					echo  '<a href = "#"><img id = "brandLogo" height = "45" src="images/logo.png" /></a>';
				}else{
					echo '<a href = "index.php"><img id = "brandLogo" height = "45" src="images/logo.png" /></a>';
				}
				echo '</span>		
				<button class="navbar-toggle" data-toggle="collapse" data-target=".navbarSec">
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				</button>
				<div class="collapse navbar-collapse navbarSec">
					<ul class="nav navbar-nav navbar-right">
						
						<li class="' . $siteOperations  . ' dropdown ' . $disabled . '"> 
							<a href="#" class="dropdown-toggle" data-toggle="dropdown">Overview<b class="caret"></b> </a>
							<ul class="dropdown-menu">
								<li><a href="summary.php">Summary </a></li>
								<li><a href="statistics.php">Statistics</a></li> 
							</ul>
						</li>

						<li class="' . $wrList  . ' dropdown ' . $disabled . '"> 
							<a href="#" class="dropdown-toggle" data-toggle="dropdown">Waiting Room<b class="caret"></b> </a>
							<ul class="dropdown-menu">
								<li> <a href="wrlist.php">WaitingRoom List</a></li>
								<li> <a href="morgue.php">Morgue List</a></li>
								<li><a href="addsite.php">Add / Remove Site</a></li>
							</ul>
						</li>
						
						<li class="dropdown ' . $disabled . '"> 
							<a href="#" class="dropdown-toggle" data-toggle="dropdown">Site Readiness<b class="caret"></b> </a>
							<ul class="dropdown-menu">
								<li> <a target = "new" href="https://dashb-ssb.cern.ch/dashboard/request.py/siteview?view=site_readiness#currentView=Site+Readiness&highlight=true">SSB</a></li>
								<li> <a target = "new" href="http://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadiness/HTML/SiteReadinessReport.html">SR Report</a></li>
							</ul>
						</li>
						
						
						<li class="dropdown ' . $disabled . '"> 
							<a href="#" class="dropdown-toggle" data-toggle="dropdown">Site Support Team<b class="caret"></b> </a>
							<ul class="dropdown-menu">
								<li> <a target = "new" href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSiteSupportTeam">Description</a></li>
								<li> <a target = "new" href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/SiteSupportDocumentation">Documentation</a></li>
								<li> <a target = "new" href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/SiteSupportMeeting">Meeting</a></li>
								<li> <a  href="mailto:cms-comp-ops-site-support-team@cern.ch">Email</a></li>
							</ul>
						</li> ';

						/***************************************search form************************************************/
						if ($searchForm == true){
							echo '
							<li>
								<a href="#collapseOne" data-toggle="modal" data-target=".bs-example-modal-sm" class="dropdown-toggle" data-toggle = "collapse"><b class="glyphicon glyphicon-search"></b> Search</a>
							</li>
						';}
					/*********************************************************************************************************/
					include("data/connect.php");
					$query = mysql_query("SELECT * FROM notification where readStatus = 'False'");
					if(mysql_affected_rows() <= 0){
					}else{
					
					while ($notiData = mysql_fetch_array($query)){
						$notificationID[] 	 = $notiData['notificationID'];
						$notficationHead[]   = $notiData['notificationHead'];
						$notficationDetail[] = $notiData['notificationDetail']; 
						$notficationreadStatus[] = $notiData['readStatus'];				
						}
							$count = count($notificationID);
					echo ' 
							<li class="' . $notif  . ' dropdown ' . $disabled . '"> 
							<a href="#" class="dropdown-toggle" data-toggle="dropdown">
								<span class="glyphicon glyphicon-globe globe"></span> 
								<span class = "badge notification"><span class="badge-notification">'
								. $count
								. '</span></a>
							<ul class="dropdown-menu">';
								
								foreach($notficationHead as $head){
								 echo '<li><a href="notifications.php">' . $head .  '</a></li>';
								}
							echo '</ul></li>'; 
						}

	/**************************************************This is example to create a menu in navbar.********************************************************************/
				/*	echo'
							<li class="dropdown ' . $disabled . '"> 
							<a href="#" class="dropdown-toggle" data-toggle="dropdown">Menu Name<b class="caret"></b> </a> <!--menu-->
							<ul class="dropdown-menu"> <!--SubMenus-->
								<li> <a target = "new" href="#">SubMenu Name1</a></li>
								<li> <a target = "new" href="#">SubMenu Name2</a></li>
		 						<li> <a target = "new" href="#">SubMenu Name3</a></li>
							</ul>
						</li>
						';
	/**************************************************************************************************************************************************************************/




				echo	'</ul>				
				</div>
			</div>
		</nav>
		';
	}

/*
 *  *************************************end of menu function **********************************************************************************
 */

 
 
 
	function getHeadline($headLine){
		echo '<h4 class= "summary_headline" align="center">' . $headLine . '</h4>';
	}

	static function getFooter(){
		echo '		
		<div class="navbar navbar-default navbar-fixed-bottom">
			<div class="container">
			<ol class="breadcrumb pull-right">
				<li> <a id ="footerLink"  target = "new" href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/SiteSupportDocumentation">Documentation</a></li>
				<li> <a id ="footerLink"  target = "new" href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/SiteSupportMeeting">Meeting</a></li>
				<li> <a id ="footerLink"  href="mailto:cms-comp-ops-site-support-team@cern.ch">Email</a></li>
			 </ol>	
			<ol class="breadcrumb pull-left">
				<li> <a id ="footerLink"  target = "new" href="https://dashb-ssb.cern.ch/dashboard/request.py/siteview?view=site_readiness#currentView=Site+Readiness&highlight=true">SSB</a></li>
				<li> <a id ="footerLink"  target = "new" href="http://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadiness/HTML/SiteReadinessReport.html">SR Report</a></li>
			 </ol>	
				
			</div>
		</div>
		';
	}

	function getRow($chartName, $headLine, $SubheadLine = null, $conditionButton = false, $summaryList = false, $chartTypeBtn = 'BPL', $chartRotateBtn = false, $chartDateBtn = false ){
//	function getRow($chartName, $headLine, $SubheadLine = null, $conditionButton = false, $summaryList = false, $chartButton = false){
		$chartId  			  = $chartName . "Chart";
		$listHead 			  = $chartName . "ListHead";
		$siteList 			  = $chartName . "SiteList";
		$listSum  			  = $chartName . "ListSum";
		$spanEndDate 		       = $chartName ."EndDate";
		$spanStartDate 		       = $chartName ."StartDate";
		$jsonSaveBtn                 = $chartName . "JsonSaveBtn";
		$csvSaveBtn                   = $chartName . "CsvSaveBtn";
		$searchText		   	           = $chartName . "searchBtn";
		$SubheadLineDateID     = $chartName . "SubheadLineDate";
		$SubheadLineID    	  = $chartName . "SubheadLine";

	if ($summaryList != true) {$gridCols = "col-md-12";} else {$gridCols = "col-md-8";}

echo '
	<div class="row">
		<div class="col-md-12">
			<div class="container">
				<div class="row">
					<div class="col-md-8">
						<h3>'  . $headLine . ' <span id = "' . $SubheadLineID . '">' . $SubheadLine . '</span> <h5><span id ="' . $SubheadLineDateID . '"> </span></h5></h3>';

				if ($conditionButton == true){

	echo '	
					<div class="btn-group chartSelect" id = "'. $chartName . 'ChartTierBtnGroup">
					  <button type="button" class="btn btn-info btn-sm dropdown-toggle" id = "' . $chartName . 'chartTierBtn" data-toggle="dropdown">
					   Tier
					   <span class="caret"></span>
					  </button>
					  <ul class="dropdown-menu" role="menu">';
						echo '<li><a class= "chartTierBtn" id="' . $chartName . 'chartT1 ">T1</a></li>';
						echo '<li><a class= "chartTierBtn" id="' . $chartName . 'chartT2 ">T2</a></li>';
						echo '<li><a class= "chartTierBtn" id="' . $chartName . 'chartT12">T1/T2</a></li>';
						
					echo '</ul>';
					echo '<span class = "queryCode" id="' . $chartName . 'queryCodeTier">T2</span>';
					echo '</div> ';

					echo '	
					<div class="btn-group conditionSelect">
					  <button type="button" class="btn btn-info btn-sm dropdown-toggle" id = "conditionBtn" data-toggle="dropdown">
					   General Overview 
					   <span class="caret"></span>
					  </button>
					  <ul class="dropdown-menu" id = "conditionDropDown" role="menu">';
						  echo '<li><a class= "chartconditionalBtn" id="' . $chartName . 'chartgener00G">General Overview</a></li>'; 
						  echo '<li><a class= "chartconditionalBtn" id="' . $chartName . 'chartabove80A"><b>Above 80%</b>Overview</a></li>';
						  echo '<li><a class= "chartconditionalBtn" id="' . $chartName . 'chartbelow80B"><b>Below 80%</b> Overview</a></li>'; 
					echo  '</ul> 
					</div> ';
					
					}


				if ($chartTypeBtn){
	echo '	
					<div class="btn-group chartSelect" id = "'. $chartName . 'ChartTypeBtnGroup">
					  <button type="button" class="btn btn-info btn-sm dropdown-toggle" id = "' . $chartName . 'chartBtn" data-toggle="dropdown">
					   Chart Type
					   <span class="caret"></span>
					  </button>
					  <ul class="dropdown-menu" role="menu">';

					  	$data = explode("|", $chartTypeBtn);
						if(in_array("B", $data)){
							echo '<li><a class= "chartTypeBtn" id="' . $chartName . 'chartBar">Bar Chart</a></li>';
						}
						if(in_array("P", $data)){
							echo '<li><a class= "chartTypeBtn" id="' . $chartName . 'chartPie">Pie Chart</a></li>';
						}
						if(in_array("L", $data)){
							echo '<li><a class= "chartTypeBtn" id="' . $chartName . 'chartLin">Line Chart</a></li>';
						}
					echo '</ul>';
					echo '<span class = "queryCode" id="' . $chartName . 'queryCodeType">bar</span>';
					echo '<span class = "queryCode" id="' . $chartName . 'queryCodeValueField"></span>';
					echo '</div> ';}

				if ($chartRotateBtn == true){
	echo '	
					<div class="btn-group chartSelect" id = "'. $chartName . 'ChartRotateBtnGroup">
					  <button type="button" class="btn btn-info btn-sm dropdown-toggle" id = "' . $chartName . 'chartRotateBtn" data-toggle="dropdown">
					   Chart Rotate
					   <span class="caret"></span>
					  </button>
					  <ul class="dropdown-menu" role="menu">
						<li><a class= "chartRotateBtn" id="' . $chartName . 'chartRotateTrue ">Horizontal</a></li>
						<li><a class= "chartRotateBtn" id="' . $chartName . 'chartRotateFalse">Vertical</a></li>';
					echo '</ul>';
					echo '<span class = "queryCode" id="' . $chartName . 'queryCodeRotate"></span>';
					echo '</div> '; 

				if ($summaryList == false && $chartDateBtn == true){
	echo '	
					<div class="btn-group chartSelect"  id = "'. $chartName . 'ChartDateBtnGroup">
					  <button type="button" class="btn btn-info btn-sm dropdown-toggle dateBtnSt" id = "' . $chartName . 'charDateBtn" data-toggle="dropdown">
					   Date
					   <span class="caret"></span>
					  </button>
					  <ul class="dropdown-menu dateGroup" role="menu">

				<label for="timePeriod" style="font-size:12px;">Time Period</label>
			    <select style="font-size:12px;" id = "' . $chartName . 'timePeriod" class="form-control">
			    	<option value="24h" >24 hours</option>
			    	<option value="48h" >48 hours</option>
			    	<option value="Lweek" selected>Last week</option>
			    	<option value="L2week" >Last 2 weeks</option>
			    	<option value="Lmonth" >Last month</option>
			    	<option value="L2months" >Last 2 months</option>
			    	<option value="L3months" >Last 3 months</option>
			    	<option value="custom" >Custom...</option>
				</select> 

						<li>
							<label style="font-size:12px;"  class = "btnstartDateLbl" for="' . $chartName . 'btnstartDate">Start Date</label>
							<input type="date" id="' . $chartName . 'btnstartDate" class="btnstartDate" max = "' . date('Y-m-d') . '" name="' . $chartName . 'btnstartDate" required class="form-control">
						</li>
						<li>
							<label style="font-size:12px;" class = "btnendDateLbl" for="' . $chartName . 'btnendDate">End Date</label>
							<input type="date" id="' . $chartName . 'btnendDate" class="btnendDate" max = "' . date('Y-m-d') . '" name="' . $chartName . 'btnendDate" required class="form-control">
						</li>
						<li style = "margin-top:5px;">
						 <button type="button" class="btn btn-danger btn-xs searchDateBtn" id = "' . $chartName . 'DateBtn">Search</button>
						</li>
					</ul>
					<span class = "queryCode" id="' . $chartName . 'queryCodeDate"></span>
				</div>';
					
					
				}


					echo '
					<button type="button" class="btn btn-info btn-sm chartqueryBtn" id = "' . $chartName . 'chartqueryBtn">
						<b class="glyphicon glyphicon-refresh"></b> Change View
					</button>'; }
					echo '</div> <!--col-md-4 headline-->

				</div> <!--row headline and buttonSet-->

				<div class="row">
						<div class="' . $gridCols . '">
							<div id="' . $chartId . '" style="width: 100%; height:400px; "> </div>
							<span id="' . $chartName . 'JsonCode" style="display:none;"></span>
					</div> <!--col-md-8 chart-->';

						if ($summaryList == false){	
						echo '<a class = "pull-right readinessBtn saveBtn json" id="' . $jsonSaveBtn . '"><span style="display:none";></span>JSON</a>';}
						if ($summaryList == true){	
						echo
						 '<div class="col-md-4" style = "z-index:0;">';
						 
	//*********************************************CUSTOM DATE PANL**************************************************					 
						 
echo '						 	<div class = "customDatePanel" id="' . $chartName . 'customDatePanel">
						 	<ul>
						<li>
							<label style="font-size:12px;"  class = "btnstartDateLbl" for="' . $chartName . 'btnstartDate">Start Date</label>
							<input type="date" id="' . $chartName . 'btnstartDate" class="btnstartDate" max = "' . date('Y-m-d') . '" name="' . $chartName . 'btnstartDate" required class="form-control">
						</li>

						<li>
							<label style="font-size:12px;" class = "btnendDateLbl" for="' . $chartName . 'btnendDate">End Date</label><br>
							<input type="date" id="' . $chartName . 'btnendDate" class="btnendDate" max = "' . date('Y-m-d') . '" name="' . $chartName . 'btnendDate" required class="form-control">
							
						</li>
						<li style = "margin-top:5px;">
						 <button type="button" class="btn btn-danger btn-xs searchDateBtnBox" id = "' . $chartName . 'DateBtn">Search</button>
						 <button type="button" class="btn btn-danger btn-xs searchDateBtnClose" id = "' . $chartName . 'DateBtn">Close</button>

						</li>
					</ul>
			 	</div>';
			 	
//****************************************************************************************************************************			 	
			 	if ($chartDateBtn == true){
						echo	'<h5 id ="'. $listHead .'" style = "display:none;">
								<div class = "siteListHead">
								    <select style="font-size:12px;" id = "' . $chartName . 'timePeriod" class="form-control timePeriodHead">
								    	<option value="24h" >24 hours</option>
								    	<option value="48h" >48 hours</option>
								    	<option value="Lweek" selected>Last week</option>
								    	<option value="L2week" >Last 2 weeks</option>
								    	<option value="Lmonth" >Last month</option>
								    	<option value="L2months" >Last 2 months</option>
								    	<option value="L3months" >Last 3 months</option>
								    	<option id="optionCustomID" value="custom" >Custom...</option>
									</select> 
									';


				
	echo '	
					<button type="button" class="btn btn-danger btn-xs searchDateBtn" id = "' . $chartName . 'DateBtn">Search</button>
					<span class = "queryCode" id="' . $chartName . 'queryCodeDate"></span>
				';}
									
								
								echo '</div>
								</h5>
								<div class="list-group SiteList" id="' .$siteList . '"> </div>
									<div> <h5 id ="' . $listSum . '"  class = "ListSum" style = "display:none;">Total 5 Sites </h5> 
									</div>
									<div class = "jsonSaveSection">
										<input type="text" id="' . $searchText . '" placeholder = "Search List" class="form-control pull-left findSiteText">
									<a class = "pull-right readinessBtn saveBtn json" id="' . $jsonSaveBtn . '"><span style="display:none";></span>JSON</a>
									</div>
								</div>
							</div>';}
					echo '		 
				</div> <!--row chart and list-->

			</div> <!--container body-->
		</div> <!--col-md-12 body-->
	</div> <!--row body-->';


	} // getRow
} // class

?>