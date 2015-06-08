<?php
//include ('data/connect.php');
/*! 
 *  \details   Site Support DataBase Monitoring
 *  \author    Gökhan Kandemir
 *  \version   1.0
 *  \date      2014
 *  \copyright Site Support Team
 */
class calculate
	{

		function daydiff($date1 , $date2)
			{
				$end = strtotime($date2);
				$start = strtotime($date1);
				$days_between = ceil((abs($end - $start) / 86400));
				return $days_between;

			}
			
			
		function timediff($time1 , $time2)
			{
				$end = strtotime($time2);
				$start = strtotime($time1);
				$timesBetween = ((abs($end - $start) / 3600));
				return $timesBetween;

			}
			
		function calculateMonths($sourcedate , $parameter)
			{
				$month  	= explode("-", $sourcedate);
				$month = $month[1];
				$year 		= explode("-", $sourcedate);
				$year = $year[0];
				$sourcedateM = explode("-", $sourcedate); $sourcedateM = $sourcedateM[1];
				$sourcedateD = explode("-", $sourcedate); $sourcedateD = $sourcedateD[2]; 
				$month  	= ($month == 01) ? 12 + $parameter : $month - 1 + $parameter;
				$year 		= ($sourcedateM == 01) ? $year - 1 : floor($year + ($month / 12)); 
				$month  	= ($month < 0)  ? 13 + ($month % 12) : $month % 12 + 1; 
				$day 		= min(array($sourcedateD, date( 't', mktime(0, 0, 0, $month, 1, $year))));
				return @date('Y-m-d', mktime(0,0,0,$month,$day,$year));
			}


		function checkdb($siteName)
			{
				$query = mysql_query("SELECT * FROM wr where siteName = '$siteName' ");
				if (mysql_affected_rows()) 
					{
						return "duplicate"; 
					} else return "ok";
			}

		function dateCompare($date)
			{
				$end = strtotime(date('Y-m-d')); #today
				$start = strtotime($date);
				$days_between = ceil((abs($end - $start) / 86400) / 6);
				if($days_between <= 1) 
					{
						return "x";
					}
				else
					{
						return "";
					}

			}

		function morgueInOut($date)
			{
				$end = strtotime(date('Y-m-d')); #today
				$start = strtotime($date);
				$days_between = ceil((abs($end - $start) / 86400) / 6);
				if($days_between <= 8) 
					{
						return "x";
					}
				else
					{
						return "";
					}

			}



		function calculateTotalWeek($siteName , $indate)
			{
				$end = strtotime(date('Y-m-d')); # today
				$start = strtotime($indate);
				/*$totalWeek = 0;
				$query = mysql_query("select sitename,sum(totalweek) from wrlist where siteName = '$siteName' group by siteName");
				while ($data = mysql_fetch_array($query)) 
					{
						$totalWeek = $data[1];
					}
				*/
				$days_between = ceil((abs($end - $start) / 86400) / 7);	
				//$totalWeek = $totalWeek + $days_between;
				return $days_between;
			}

		function calculateFailTest($process , $idWr , $twiki)
			{

				switch ($process) 
					{
						case 'sam':
							$query = mysql_query("select * from samfailing where idWr = '$idWr'");
							break;

						case 'hc':
							$query = mysql_query("select * from hcfailing where idWr = '$idWr'");
							break;

						case 'links':
							$query = mysql_query("select * from linksfailing where idWr = '$idWr'");
							break;

						default:
							$query = mysql_query("select * from samfailing where idWr = '$idWr'");
							break;
					}

				$exitCode = '';
				$i = 0;
				while ($data = mysql_fetch_array($query)) 
					{
						$i++;
						if ($process == 'links') 
							{
								if ($twiki == 'off')
									{
										$goodt2ft1 = ''; $goodt2tt1 = ''; $activet2ft1 = ''; $activet2tt1 = '';
										if(($data[2] != '') and ($data[2] != '-')){$goodt2ft1 =  $data[2] . ' Good T2 from T1'.'<br>';}
										if(($data[3] != '') and ($data[3] != '-')){$goodt2tt1 =  $data[3] . ' Good T2 to T1'.'<br>';}
										if(($data[4] != '') and ($data[4] != '-')){$activet2ft1 =  $data[4] . ' Active T2 from T1'.'<br>';}
										if(($data[5] != '') and ($data[5] != '-')){$activet2tt1 =  $data[5] . ' Active T2 to T1'.'<br>';}
										$exitCode = $exitCode .  $goodt2ft1 . $goodt2tt1 . $activet2ft1 . $activet2tt1;
									}
								elseif ($twiki == 'on')
									{
										
										$goodt2ft1 = ''; $goodt2tt1 = ''; $activet2ft1 = ''; $activet2tt1 = '';
										if(($data[2] != '') and ($data[2] != '-')){$goodt2ft1 =  $data[2] . ' Good T2 from T1'.'%BR%';}
										if(($data[3] != '') and ($data[3] != '-')){$goodt2tt1 =  $data[3] . ' Good T2 to T1'.'%BR%';}
										if(($data[4] != '') and ($data[4] != '-')){$activet2ft1 =  $data[4] . ' Active T2 from T1'.'%BR%';}
										if(($data[5] != '') and ($data[5] != '-')){$activet2tt1 =  $data[5] . ' Active T2 to T1'.'%BR%';}
										$exitCode = $exitCode .  $goodt2ft1 . $goodt2tt1 . $activet2ft1 . $activet2tt1;
									}
							}

						else
							{
								if ($twiki == 'off')
									{
										$exitCode = $exitCode.'<b>['.$i.'] </b>'.$data[2].'<br>';
									}
								elseif ($twiki == 'on')
									{
										$exitCode = $exitCode.'<b>['.$i.'] </b>'.$data[2].' %BR% ';
									}
							}
					}
				return $exitCode;
			}		

	}

?>