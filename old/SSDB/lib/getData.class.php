<?php
@include("./data/connect.php");
/** This class is used  to get data from dashboard or Mysql database, calculate days (waiting room, drain) or site readiness rate. **/
/*! 
 *  \details   Site Support DataBase Monitoring
 *  \author    Gökhan Kandemir
 *  \version   1.0
 *  \date      2014
 *  \copyright Site Support Team
 */
class getData 
	{
	/** This method is used to create JSON Code by using Mysql Tables for creating Most Common Errors Chart. Tables =>  sta_hcfailing_week, sta_samfailing_week, sta_linksfailing_week. [more explanation] **/
	public function getJSONfromDB($custom_Date = false, $custom_startDate = null, $custom_endDate = null, $dbName)
			{
				$islem = new calculate();
				$endDate   = $custom_endDate; 
				$startDate = $custom_startDate;
				if($dbName == 'links'){
					$prefix = '';
					$json = "[\n";
					$data = array();
				$query = "SELECT
							(case when goodT2fT1 <> '-' then goodT2fT1 end),
							(case when goodT2tT1 <> '-' then goodT2tT1 end),
							(case when activeT2fT1 <> '-' then activeT2fT1 end),
							(case when activeT2tT1 <> '-' then activeT2tT1 end),
							siteName
							from sta_linksfailing_week
							where 
							(((case when goodT2fT1 	<> '-' then goodT2fT1 	end) <> '-') or 
							((case when goodT2tT1 	<> '-' then goodT2tT1 	end) <> '-') or
							((case when activeT2fT1 <> '-' then activeT2fT1 end) <> '-') or 
							((case when activeT2tT1 <> '-' then activeT2tT1 end) <> '-')) and  weekDate between '" . $startDate . "' and '" . $endDate ."'
							";
				$result  = mysql_query($query);

				$rateGF      = 0;  /**< bad links calculation variable for Good links from*/
				$rateGT      = 0;  /**< bad links calculation variable for Good links to*/
				$countGF   = 0;  /**< bad links count variable for Good links from*/
				$countGT   = 0;  /**< bad links count variable for Good links to*/
				$countAF    = 0;  /**< bad links count variable for Active links from*/
				$countAT    = 0;  /**< bad links count variable for Active links to*/

				if($result){
					while ($row = mysql_fetch_array($result)){
							/** Calculate good links from **/
							if (trim($row[0]) != ''){ 
								$numbers = explode("/", $row[0]);
								if (($numbers[0] != 'n') && ($numbers[1] != 0)) {
									$rateGF = ($numbers[0] / $numbers[1]);
									if ($rateGF < 0.5) {
										$countGF++;
									}
								}else{
									$countGF++;
								}
							}	

							/** Calculate good links to **/
							if (trim($row[1]) != ''){
								$numbers = explode("/", $row[1]);
								if (($numbers[0] != 'n') && ($numbers[1] != 0)) {
									$rateGT = ($numbers[0] / $numbers[1]);
									if ($rateGT < 0.5) {
										$countGT++;
									}
								}else{
									$countGT++;
								}
							}	


					//**********************Active linkler Calculation******************************
							/** Calculate active links from **/
							if (trim($row[2]) != ''){
								if (($row[2] != 'n/a')) {
									$tierName = substr($row[4], 0,2);
										if ($tierName == 'T1'){
											if (intval($row[2]) < 20){
												$countAF++;
											}
										}
										if ($tierName == 'T2'){
											if (intval($row[2]) < 4){
												$countAF++;
											}
										}
								}else{
									$countAF++;
								}
							}	

							/** Calculate active links to **/
							if (trim($row[3]) != ''){
								if (($row[3] != 'n/a')) {
									$tierName = substr($row[4], 0,2);
										if ($tierName == 'T2'){
											if (intval($row[3]) < 2){
												$countAT++;
											}
										}
								}else{
									$countAT++;
								}
							}	
					//*****************************************************************************************
							
					} // while..
					@$data['gF'] = $countGF;
					@$data['gT'] = $countGT;
					@$data['aT'] = $countAT;
					@$data['aF'] = $countAF;
				}
#_________________________JSON PREPARING_________________________________

				$json = '[
							{
								"errorname"  : "Good_T2_links_from_T1s",
								"errorcountgF" : ' . $data['gF'] . '
							},

							{
								"errorname"  : "Good_T2_links_to_T1s",
								"errorcountgT" : ' . $data['gT'] . '
							},

							{
								"errorname"  : "Active_T2_links_from_T1s",
								"errorcountaF" : ' . $data['aF'] . '
							},

							{
								"errorname"  : "Active_T2_links_to_T1s",
								"errorcountaT" : ' . $data['aT'] . '
							}
						]';
#__________________________________________________________________________
			}else{
				$query = "SELECT count(exitCode) , exitCode FROM" . " sta_" . $dbName ."failing_week where weekDate between '" . $startDate . "' and '" . $endDate ."' GROUP BY exitCode order by count(exitCode) DESC";
				$result = mysql_query($query);
				$prefix = '';
				$json = "[\n";
				if($result){
					while ( $row = mysql_fetch_array( $result ) ) {
					  $json = $json . $prefix . "{\n";
					  $json = $json . '  "siteName": "' . $row[1] . '",' . "\n";
					  $json = $json . '  "number": ' . $row[0] . '' . "\n";
					  $json = $json . " }";
					 $prefix = ",\n";
					}
					$json = $json . "\n]";
				}else{
					$json = ']';
				}
			}
			return array($json, $endDate, $startDate);
		}


		/** This method is used to get JSON Code from dashboard for Site Readiness, Waiting room, Drain. Metrics (45, 153, 158) **/ 
		public function getJSON($parameter, $custom_Date = false, $custom_startDate = null, $custom_endDate = null, $metric = null, $tier = null){			
			$islem = new calculate();
			$endDate   = ($custom_Date == false) ? date('Y-m-d') /*today*/ : $custom_endDate;
			$startDate = ($custom_Date == false) ? $islem->calculateMonths($endDate , $parameter) /* 1 month 2 months 3 months */ : $custom_startDate;
			
			if($metric == 153){ /** Waiting Room **/
				$url = 'http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=153&time=custom&dateFrom=' . $startDate . '&dateTo=' . $endDate . '&site=T2_AT_Vienna&sites=' . $tier . '&clouds=undefined&batch=1';
			}
		
			if($metric == 158){ /** Drain **/
				$url = 'http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=158&time=custom&dateFrom=' . $startDate . '&dateTo=' . $endDate . '&site=T0_CH_CERN&sites=' . $tier . '&clouds=undefined&batch=1';
			}
		
			if($metric == 45){ /** Site Readiness **/
				$url = 'http://dashb-ssb.cern.ch/dashboard/request.py/getplotdata?columnid=45&time=custom&dateFrom=' . $startDate . '&dateTo=' . $endDate . '&site=T2_CH_CERN_T0&sites=' . $tier . '&clouds=undefined&batch=1';
			}

			$curl = curl_init();
			curl_setopt($curl, CURLOPT_URL , $url);
			curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
			$result = curl_exec($curl);
			curl_close($curl);
			return @array($result, $endDate, $startDate);
		}

		/** This method is used to get morgue list from Mysql Database**/
		private function getMorgueList(){
			$morgueList = array();
			$query = mysql_query("SELECT siteName FROM wr WHERE morgue = 'x' ORDER BY siteName ASC");
			if($query)
				{
					while($data = mysql_fetch_assoc($query)){
							$morgueList[] = $data['siteName'];
						}
				}		
			return @$morgueList;
		}

		/** This submethod is used to create JSON code for charts.**/
		private function createJSON($sites, $valueField , $chartName = null){ // $sites is array... //chartName = morgue. To prevent show 
			$jsonCode = '';
			if ($chartName == 'morgue'){
				$waitingRoomList = $this->getMorgueList();
			}
	
			foreach ($sites as $siteItems => $itemsValue)
				{
					if ($chartName == 'morgue'){
						if (!(in_array($siteItems, $waitingRoomList))){
							$tempValue = ($valueField == 'average') ? ceil($itemsValue * 100) : $itemsValue;
							$tempCode = "{\"siteName\":" . "\"$siteItems\"" . "," . "\"" . $valueField . "\":" . $tempValue . "}";
							$jsonCode = $jsonCode.$tempCode;
						}
					}else{
						$tempValue = ($valueField == 'average') ? ceil($itemsValue * 100) : $itemsValue;
						$tempCode = "{\"siteName\":" . "\"$siteItems\"" . "," . "\"" . $valueField . "\":" . $tempValue . "}";
						$jsonCode = $jsonCode.$tempCode;
						
					}
				}
	
			$jsonCode = "[" . $jsonCode . "]";
			$jsonCode = str_replace("}{", "},{", $jsonCode);
			$tempCode = json_decode($jsonCode, true);
			sort($tempCode); 
			$jsonCode = json_encode($tempCode);
			return @$jsonCode;
		}
		/** This method is used to calculate days regarding Drain, Waiting Room, Site Readiness **/
		private function getNumberofDays($jsonData, $startDate, $endDate, $colorName){
			$islem = new calculate();	
			foreach (@$jsonData[csvdata] as $key){
				$days = 0;
				if (@$key[COLORNAME] == $colorName) {
					$starttime 	 = explode('T' , @$key[Time]);
					$starttime = $starttime[0];
					$endtime     = explode('T' , @$key[EndTime]);
					$endtime = $endtime[0];
					@$sitesAll[@$key[VOName]]+= $islem->daydiff($endtime, $starttime); //To get all values of site
					if ($startDate > $starttime){
						if ($startDate > $endtime) {continue;}
						elseif ($startDate < $endtime){
							if ($startDate > $starttime){	
								$days = $islem->daydiff($endtime, $startDate);
							}
							elseif ($startDate <= $starttime){
								$days = $islem->daydiff($endtime, $starttime);
							}
						}
					}
					elseif ($startDate <= $starttime){
						$days = $islem->daydiff($endtime, $starttime);
					}
					
					if ($endtime > $endDate){
						if ($startDate > $starttime){
							$days = $islem->daydiff($endDate, $startDate);
						}
						if ($starttime > $startDate){
						 	if ($starttime > $endDate) {continue;}
						 	else{
							 		$days = $islem->daydiff($endDate, $starttime);
						 	}
					 	}
					}
					@$sites[@$key[VOName]]+=  $days; 
				}	
			} //foreach 		
			return array(@$sites, @$sitesAll);
		} //getnumberofdays
		
		/** This method is used to create JSON code for charts. To do this, method uses submethod called createJSON() **/
		public function getJSONtoData($jsonData, $startDate, $endDate, $average = false, $colorName = null, $condition = 0, $tier = null, $chartName = null){ // if average = true => calculate more three variable 
			$jsonCode = '';
			$jsonCodeAll = '';
			$tempCode = '';
			$sites = array();
			$sitesAll = array();
			if ($average == false) {
				list($sites, $sitesAll) = $this->getNumberofDays($jsonData, $startDate, $endDate, $colorName);
				return array($this->createJSON($sites, "Days", $chartName), $this->createJSON($sitesAll, "Days"));// create JSON for 1,2,3 months results //create JSON All months.
			}else{
				list($sitesGreen)  = $this->getNumberofDays($jsonData, $startDate, $endDate, 'green');
				list($sitesYellow) = $this->getNumberofDays($jsonData, $startDate, $endDate, 'yellow');
				list($sitesBrown)  = $this->getNumberofDays($jsonData, $startDate, $endDate, 'brown');
				$sitesSR     = $this->average($sitesGreen, $sitesYellow, $sitesBrown, $startDate, $endDate, $condition, $tier);
				return  $this->createJSON($sitesSR, "average", $chartName); // create JSON for 1,2,3 months results //create JSON All months.
			}
		}
		
	/** This method is used to calculate Site Readiness Rate.  **/	
		private function average($sitesGreen, $sitesYellow, $sitesBrown, $startDate, $endDate, $condition, $tier){
			if ($tier == 'T2'){ 
				$sitesList = array('T2_AT_Vienna','T2_BE_IIHE','T2_BE_UCL','T2_BR_SPRACE','T2_BR_UERJ','T2_CH_CERN', 'T2_CH_CSCS','T2_CN_Beijing','T2_DE_DESY','T2_DE_RWTH','T2_EE_Estonia','T2_ES_CIEMAT','T2_ES_IFCA','T2_FI_HIP','T2_FR_CCIN2P3','T2_FR_GRIF_IRFU','T2_FR_GRIF_LLR','T2_FR_IPHC','T2_GR_Ioannina','T2_HU_Budapest','T2_IN_TIFR','T2_IT_Bari','T2_IT_Pisa','T2_IT_Legnaro','T2_IT_Rome','T2_KR_KNU','T2_MY_UPM_BIRUNI','T2_PK_NCP','T2_PL_Warsaw','T2_PT_NCG_Lisbon','T2_RU_IHEP','T2_RU_INR','T2_RU_ITEP','T2_RU_JINR','T2_RU_PNPI','T2_RU_RRC_KI','T2_RU_SINP','T2_TH_CUNSTDA','T2_TR_METU','T2_TW_Taiwan','T2_UA_KIPT','T2_UK_London_Brunel','T2_UK_London_IC','T2_UK_SGrid_Bristol','T2_UK_SGrid_RALPP','T2_US_Caltech','T2_US_Florida','T2_US_MIT','T2_US_Nebraska','T2_US_Purdue','T2_US_UCSD','T2_US_Vanderbilt','T2_US_Wisconsin');
				}
			if ($tier == 'T0/1'){ 
				$sitesList = array('T2_CH_CERN', 'T1_DE_KIT', 'T1_ES_PIC', 'T1_FR_CCIN2P3', 'T1_IT_CNAF', 'T1_RU_JINR', 'T1_TW_ASGC', 'T1_UK_RAL', 'T1_US_FNAL');}
	
			if ($tier == 'all' || $tier == 'T0/1/2'){ 
				$sitesList = array('T1_DE_KIT', 'T1_ES_PIC', 'T1_FR_CCIN2P3', 'T1_IT_CNAF', 'T1_RU_JINR', 'T1_TW_ASGC', 'T1_UK_RAL', 'T1_US_FNAL', 'T2_AT_Vienna','T2_BE_IIHE','T2_BE_UCL','T2_BR_SPRACE','T2_BR_UERJ','T2_CH_CERN','T2_CH_CSCS','T2_CN_Beijing','T2_DE_DESY','T2_DE_RWTH','T2_EE_Estonia', 'T2_ES_CIEMAT','T2_ES_IFCA', 'T2_FI_HIP', 'T2_FR_CCIN2P3', 'T2_FR_GRIF_IRFU', 'T2_FR_GRIF_LLR', 'T2_FR_IPHC', 'T2_GR_Ioannina','T2_HU_Budapest','T2_IN_TIFR','T2_IT_Bari','T2_IT_Pisa','T2_IT_Legnaro', 'T2_IT_Rome', 'T2_KR_KNU','T2_MY_UPM_BIRUNI','T2_PK_NCP', 'T2_PL_Warsaw','T2_PT_NCG_Lisbon', 'T2_RU_IHEP','T2_RU_INR','T2_RU_ITEP','T2_RU_JINR', 'T2_RU_PNPI','T2_RU_RRC_KI','T2_RU_SINP', 'T2_TH_CUNSTDA','T2_TR_METU','T2_TW_Taiwan','T2_UA_KIPT','T2_UK_London_Brunel', 'T2_UK_London_IC','T2_UK_SGrid_Bristol', 'T2_UK_SGrid_RALPP','T2_US_Caltech','T2_US_Florida','T2_US_MIT', 'T2_US_Nebraska', 'T2_US_Purdue', 'T2_US_UCSD', 'T2_US_Vanderbilt','T2_US_Wisconsin');}
	
			$month = explode("-", $startDate);
			$month = $month[1];
			$count = 0;
			$sitesSR = array();
			$islem = new calculate();
			$percentage = $condition / 100;
			$totalDays = $islem->daydiff($startDate , $endDate);
			foreach ($sitesList as $items => $ItemsValues){
				$SR = 0;
				$R_Values  = 0;
				$W_Values  = 0;
				$SD_Values = 0;
				$average   = 0;
				if (@array_key_exists($ItemsValues, $sitesGreen))  {$R_Values  = $sitesGreen[$ItemsValues];}
				if (@array_key_exists($ItemsValues, $sitesYellow)) {$W_Values  = $sitesYellow[$ItemsValues];}
				if (@array_key_exists($ItemsValues, $sitesBrown))  {$SD_Values = $sitesBrown[$ItemsValues];}
				@$SR = ($R_Values + $W_Values) / ($totalDays - $SD_Values);
				if ($condition > 0) {
					if ($condition == 60) {if($SR >= $percentage) {@$sitesSR[$ItemsValues] = $SR;}}  // SR threshold above  60% for T1 				
					if ($condition == 59) {if($SR  < $percentage)  {@$sitesSR[$ItemsValues] = $SR;}}  // SR threshold below  60% for T1				
					if ($condition == 80) {if($SR >= $percentage) {@$sitesSR[$ItemsValues] = $SR;}}  // SR threshold above  80% for T2				
					if ($condition == 79) {if($SR  < $percentage)  {@$sitesSR[$ItemsValues] = $SR;}}  // SR threshold below  80% for T3				
				}else{
					@$sitesSR[$ItemsValues] = $SR;				
				}
			}
			return @$sitesSR;
		}
		
	}
?>