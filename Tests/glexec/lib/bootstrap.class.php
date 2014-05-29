<?php
class bootstrap{

/* 		
 * ****************************** This function is used for creating menu - submenu *******************************************************************
 */
	static function getNavBar($searchForm = false, $active = null, $brand = null, $disabled = false){
		$home = ''; $siteOperations = ''; $wrList = ''; ; $notif = '';
		if ($active == 'siteop') {$siteOperations = 'active';};
		echo '
		<nav class="navbar navbar-inverse navbar-static-top" id = "sidebar">
			<div class="container">
				<span class="navbar-brand navbar-image brand_Headline">';
				if($disabled == 'disabled'){
					echo  '<a href = "#"><img id = "brandLogo" height = "45" src="css/logo.png" /></a>';
				}else{
					echo '<a href = "index.php"><img id = "brandLogo" height = "45" src="css/logo.png" /></a>';
				}
				echo '</span>		
				<button class="navbar-toggle" data-toggle="collapse" data-target=".navbarSec">
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				</button>
				<div class="collapse navbar-collapse navbarSec">
					<ul class="nav navbar-nav navbar-right">
						
						<li class="dropdown"> 
							<a href="#" class="dropdown-toggle" data-toggle="dropdown">Site Readiness<b class="caret"></b> </a>
							<ul class="dropdown-menu">
								<li> <a target = "new" href="https://dashb-ssb.cern.ch/dashboard/request.py/siteview?view=site_readiness#currentView=Site+Readiness&highlight=true">SSB</a></li>
								<li> <a target = "new" href="http://cms-site-readiness.web.cern.ch/cms-site-readiness/SiteReadiness/HTML/SiteReadinessReport.html">SR Report</a></li>
							</ul>
						</li>
						
						<li class="dropdown"> 
							<a href="#" class="dropdown-toggle" data-toggle="dropdown">Site Support Team<b class="caret"></b> </a>
							<ul class="dropdown-menu">
								<li> <a target = "new" href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/CompOpsSiteSupportTeam">Description</a></li>
								<li> <a target = "new" href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/SiteSupportDocumentation">Documentation</a></li>
								<li> <a target = "new" href="https://twiki.cern.ch/twiki/bin/view/CMSPublic/SiteSupportMeeting">Meeting</a></li>
								<li> <a  href="mailto:cms-comp-ops-site-support-team@cern.ch">Email</a></li>
							</ul>
						</li>
					</ul>				
				</div>
			</div>
		</nav>
		';
	}

/*
 *  *************************************end of menu function **********************************************************************************
 */

	static function getHeadline($headLine){
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
} // class

?>