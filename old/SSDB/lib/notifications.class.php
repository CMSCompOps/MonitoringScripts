<?php
/*! 
 *  \details   Site Support DataBase Monitoring
 *  \author    Gökhan Kandemir
 *  \version   1.0
 *  \date      2014
 *  \copyright Site Support Team
 */
class notifications{

	public function getWRfromDB(){
	
		$waitingRoomList = array();
		$wrDBStr = '';
		$query = mysql_query("SELECT siteName FROM wr WHERE morgue = '' ORDER BY siteName ASC");
		if($query)
			{
				while($data = mysql_fetch_assoc($query)){
						$waitingRoomList[] = $data['siteName'];
						$wrDBStr  = $wrDBStr . $data['siteName']  . "<br>";
					}
			}		
			return array(@$waitingRoomList, @$wrDBStr);
	}


	public function getMorguefromDB(){
		$waitingRoomList = array();
		$wrDBStr = '';
		$inDate = '';
		$query = mysql_query("SELECT siteName, inDate FROM wr WHERE morgue = '' ORDER BY siteName ASC");
		if($query)
			{
				while($data = mysql_fetch_assoc($query)){
						$waitingRoomList[] = $data['siteName'];
						$inDate[] = $data['inDate'];
						$wrDBStr  = $wrDBStr . $data['siteName']  . "<br>";
					}
			}		
			return array(@$waitingRoomList,@$inDate, @$wrDBStr);
	}

	
	
	public function getWRfromSSB($morgue = "morgue"){
		$operation = new getData();
		$wrSSBStr = '';
		list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-0 day", time() - 86400)), date('Y-m-d'),  153, 'T1');
		$jsonData = json_decode($result, true);
		list($jsonCode, $jsonCodeAll) = $operation->getJSONtoData($jsonData, $startDate, $endDate, false, 'red', 0, '', $morgue);
		$tmpWR = json_decode($jsonCode, true);
		foreach($tmpWR as $key => $value){
			$wrSSB[$key] = $tmpWR[$key]['siteName'];
			$wrSSBStr 	 = $wrSSBStr  . $tmpWR[$key]['siteName']. "<br>";
		}
		unset($operation);
		
		return array($wrSSB,$wrSSBStr);
		
	}
	
	public function getDrainfromSSB(){
		$operation = new getData();
		$drainSSBStr = '';
		list($result, $endDate, $startDate) = $operation->getJSON(0, true , date('Y-m-d', strtotime("-0 day", time() - 86400)), date('Y-m-d'),  158, 'T2');
		$jsonData = json_decode($result, true);
		list($jsonCode, $jsonCodeAll) = $operation->getJSONtoData($jsonData, $startDate, $endDate, false,  'yellow');
		$tmpDrain = json_decode($jsonCode, true);
		foreach($tmpDrain as $key => $value){
			$drainSSB[$key]  = $tmpDrain[$key]['siteName'];
			$drainSSBStr 	 = $drainSSBStr  . $tmpDrain[$key]['siteName']. "<br>";
		}
		unset($operation);
		return array($drainSSB,$drainSSBStr);
		
	}

	public function checkNotifications(){
		#______________________________________wrSB ile SSB karsilastirmasi___________________________________
		include("lib/errorstr.php"); // messages
		$op = new notifications();
		$message = '';
		list($wrDB,$wrDBStr)  = $op->getWRfromDB();
		list($wrSSB,$wrSSBStr) = $op->getWRfromSSB();
		
		if (count($wrDB) != count($wrSSB)){
		
			$message = @$error['wrCrsh']."\n\n" 
			  	 	   . "<b>Waiting Room List in SSB (metric 153) (without morgue)</b> \n"
					   . $wrSSBStr . "\n"
					   . "<b>Waiting Room List in DB (without morgue)</b>\n"
					   . $wrDBStr;
			#____________________________________Record to DB__________________________________________________
			
			#____________________________________Check DB for Same notification on Today_______________________
			$query = mysql_query("SELECT * from notification where notificationDetail = '$message' and notificationDate > DATE_SUB(curdate(), INTERVAL 1 DAY)");
			if(mysql_affected_rows() > 0){
				//Because The Same notification is already in Notifications, don't save this notification
			}else{
				$insert = mysql_query("INSERT INTO notification SET
				notificationID = 'wrCrsh',
				notificationHead = 'Waiting Room doesn`t match',
				notificationDetail = '$message',
				notificationDate  = CURDATE()
				");
				if(!$insert){
					// send email error
				}
			#_________________________________________________________________________________________________
			}
		}
		#_____________________________________________________________________________________________________
		
		
		
		#___________________________________morgue kontrolü___________________________________________________
		
		$opDate = new calculate();
		$movedSites = '';
		list($wrDB, $inDate, $wrDBStr)  = $op->getMorguefromDB();
		
			foreach($wrDB as $key => $wrDBValue){
				if($opDate->calculateTotalWeek('', $inDate[$key]) > 19){ // if the site(s) is older than 20 weeks. Give a Notification.
					$movedSites = $movedSites . $wrDBValue . "<br>";
				}
			}
		
			if ($movedSites != ''){
				$message = @$error['morgue']."\n\n" 
			   . "<b>The Sites have to move into Morgue</b> \n"
			   . $movedSites;
			#____________________________________Record to DB__________________________________________________
			
			#____________________________________Check DB for Same notification on Today_______________________
				$query = mysql_query("SELECT * from notification where notificationDetail = '$message' and notificationDate > DATE_SUB(curdate(), INTERVAL 1 DAY)");
				if(mysql_affected_rows() > 0){
					//Because The Same notification is already in Notifications, don't save this notification
				}else{
					$insert = mysql_query("INSERT INTO notification SET
					notificationID = 'morgue',
					notificationHead = 'Move into Morgue',
					notificationDetail = '$message',
					notificationDate  = CURDATE()
					");
					if(!$insert){
						// send email error
					}
				#_________________________________________________________________________________________________
				}
			}
		
		#_____________________________________________________________________________________________________
		
		
		#___________________________________meeting Page kontrolu_____________________________________________
		$day = date('l', strtotime(date('Y-m-d')));
		if ($day == 'Friday'){
			$message = @$error['metPage'] . "\n\n" .'<a target = "new" href ="https://twiki.cern.ch/twiki/bin/view/CMSPublic/SiteSupportMeeting">Meeting Page</a>';
			#____________________________________Record to DB__________________________________________________
			
			#____________________________________Check DB for Same notification on Today_______________________
				$query = mysql_query("SELECT * from notification where notificationDetail = '$message' and notificationDate > DATE_SUB(curdate(), INTERVAL 1 DAY)");
				if(mysql_affected_rows() > 0){
					//Because The Same notification is already in Notifications, don't save this notification
				}else{
					$insert = mysql_query("INSERT INTO notification SET
					notificationID = 'metPage',
					notificationHead = 'Site Support Meeting Page',
					notificationDetail = '$message',
					notificationDate  = CURDATE()
					");
					if(!$insert){
						// send email error
					}
				#_________________________________________________________________________________________________
				}
		}
		#_____________________________________________________________________________________________________
		
		
		#___________________________________Drain List ile WR List Karşılaştırması____________________________
		
		list($wrSSB,$wrSSBStr) = $op->getWRfromSSB('');
		list($drainSSB,$drainSSBStr) = $op->getDrainfromSSB();
		
		if (count($drainSSB) != count($wrSSB)){
		
			$drainList = '';
			foreach($wrSSB as $wrDBValue){
				if(!(in_array($wrDBValue, $drainSSB))){
					$drainList = $drainList . $wrDBValue . "<br>";
				}
			}
		
			$message = @$error['wrDrn']."\n\n" 
			  	 	   . "<b>Waiting Room List in SSB (metric 153)</b> \n"
					   . $wrSSBStr . "\n"
					   . "<b>Drain List in SSB (metric 158) </b>\n"
					   . $drainSSBStr . "\n"
					   . "<b>The Site(s) doesn`t match with Drain </b>\n"
					   . $drainList;
		
		#_____________________________________________________________________________________________________
		
			#____________________________________Record to DB__________________________________________________
			
			#____________________________________Check DB for Same notification on Today_______________________
			$query = mysql_query("SELECT * from notification where notificationDetail = '$message' and notificationDate > DATE_SUB(curdate(), INTERVAL 1 DAY)");
			if(mysql_affected_rows() > 0){
				//Because The Same notification is already in Notifications, don't save this notification
			}else{
				$insert = mysql_query("INSERT INTO notification SET
				notificationID = 'wrDrn',
				notificationHead = 'Check Waiting Room & Drain',
				notificationDetail = '$message',
				notificationDate  = CURDATE()
				");
				if(!$insert){
					// send email error
				}
			#_________________________________________________________________________________________________
			}
		}
		#_____________________________________________________________________________________________________
		unset($op);
	}


} // end of class

?>