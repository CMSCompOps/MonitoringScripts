<?php

	function getJSONfromURL($url){
		$curl = curl_init();
		curl_setopt($curl, CURLOPT_URL, $url);
		curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
		$result = curl_exec($curl);
		curl_close($curl);
		$json = json_decode($result, true);
		return $json;
	}
	

	function getXMLfromURL($url){
		$curl = curl_init();
		curl_setopt($curl, CURLOPT_URL , $url);
		curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
		$xml = curl_exec($curl);
		curl_close($curl);
		return $xml;
	}


	function getMessage($hostName){
		error_reporting(0);	
		$url = "http://dashb-cms-sum.cern.ch/dashboard/request.py/getTestResults?profile_name=CMS_CRITICAL_FULL&hostname=" . $hostName. "&flavours=CREAM-CE,SRMv2&metrics=org.cms.glexec.WN-gLExec,org.cms.glexec.WN-gLExec,org.cms.glexec.WN-gLExec,org.cms.glexec.WN-gLExec&time_range=last12&start_time=undefined&end_time=undefined";
		$json = getJSONfromURL($url);
		$warningID  = array();
		$okID           = array();
		$errorID       = array();
		foreach($json["data"] as $key => $value){
			foreach($value as $keyy => $valuee){
				 foreach($valuee as $keyyy => $valueee) {
					if(strstr($valueee[1], "OK")){
						$okID[] =  $valueee[0];
					}else {
						$warningID [] = $valueee[0];
					} // if OK or WARNING
				} // foreach valueee
			} // foreach valuee
		} // foreach value
		foreach($json["urls"] as $urlKey => $urlValue){
			foreach($urlValue as $urlChildKey => $urlChildValue){
				if (in_array($urlChildKey, $warningID)){
					$xml = getXMLfromURL("http://dashb-cms-sum.cern.ch/dashboard/request.py/" . $urlChildValue);
					$logOnlyMode = "Warning: Same /usr/bin/id for payload and pilot";
					if (!strstr($xml, $logOnlyMode)){
						$errorID[$urlChildKey] = "http://dashb-cms-sum.cern.ch/dashboard/request.py/" . $urlChildValue;
					} // if logOnlyMode
				} // if in_array warningID
			} // foreach urlValue 
		}
		return array($errorID, $okID);
	} // function getMessage

	
	function getAllCE(){
		$countTotalSite = 0;
		$data =  getXMLfromURL("http://grid-monitoring.cern.ch/myegi/sam-pi/latest_metric_results_in_profile/?vo_name=cms&profile_name=CMS_CRITICAL_FULL&service_hostname=&service_flavour=CREAM-CE");
		$xml = simplexml_load_string($data);
		$siteList = array();
		$glexecList = array();
		$countT1s = 0;
		$countT2s = 0;
		foreach($xml->Profile->Group as $site){
			$countTotalSite++;
			$siteName = (string)$site["name"];
			if (substr($siteName, 0,2) == 'T1') {$countT1s++;}
			if (substr($siteName, 0,2) == 'T2') {$countT2s++;}
			$countService = count($site->Service);
			if ($countService > 0){
				for ($j=0; $j < $countService; $j++) { 
					if($site->Service[$j]->Metric){
						$countMtr = count($site->Service[$j]->Metric);
						$hostName = (string)$site->Service[$j]['hostname'];
						@$siteList[$siteName][] = $hostName;
					} // if site->Services->Metric
				} // for services
				//echo  "<hr>"; 
			} // for countServices
		} // site foreach
		ksort($siteList);
		return array($siteList, $countT1s, $countT2s);
	} //function getAllCE

	
	function getGLEXEC($siteList){
		$countT1sProblem = 0;
		$countT2sProblem = 0;	
		$siteFlag = '';
		foreach($siteList as $siteName => $hostName){
			if((substr($siteName, 0,2) == 'T1') || (substr($siteName, 0,2) == 'T2')){
				foreach($hostName as $hostKey){
					list($errorID, $okID) = getMessage($hostKey);
					if (!(empty($errorID)) || !(empty($okID))){
					if(count($errorID) >= count($okID)){
						$dashboardUrl = "http://dashb-cms-sum.cern.ch/dashboard/request.py/historicalsmryview-sum#view=test&time%5B%5D=last12&granularity%5B%5D=default&profile=CMS_CRITICAL_FULL&group=AllGroups&site%5B%5D=" 
						. $siteName 
						. "&flavour%5B%5D=All+Service+Flavours&disabledFlavours=true&metric%5B%5D=org.cms.glexec.WN-gLExec&metric%5B%5D=org.cms.glexec.WN-gLExec&metric%5B%5D=org.cms.glexec.WN-gLExec&metric%5B%5D=org.cms.glexec.WN-gLExec&disabledMetrics=true&host%5B%5D="
						. $hostKey;
						$glexecList[$siteName][$hostKey] = $dashboardUrl;
						if($siteFlag != $siteName){
							if (substr($siteName, 0,2) == 'T1') {$countT1sProblem++;}
							if (substr($siteName, 0,2) == 'T2') {$countT2sProblem++;}
							$siteFlag = $siteName;	
						}
					}}
				} // foreeach hostName
			} // if siteName T1 or T2
		} // foreach siteList
		return array($glexecList, $countT1sProblem, $countT2sProblem);
	}
?>