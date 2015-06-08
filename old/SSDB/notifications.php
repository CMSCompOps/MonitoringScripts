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
	bootstrap::getNavBar(false, 'notif', 'Notifications');
	bootstrap::getHeadLine('Notifications');
	
?>

<!--*********************************************************************************************-->	
	<div class="container">
		<?php 
			include("data/connect.php");
			$query = mysql_query("SELECT * FROM notification where readStatus = 'False'");
			if(mysql_affected_rows() <= 0){
				echo '<div class="alert alert-warning">You don\'t have any notifications.</div>';
			}else{
		?>
		<ul class="list-group notification-list">
<!--*******************************************************************************************-->
		<?php   
			
			while ($notiData = mysql_fetch_array($query)){
				$notificationID[] 	 = $notiData['notificationID'];
				$notficationHead[]   = $notiData['notificationHead'];
				$notficationDetail[] = $notiData['notificationDetail']; 
				$notficationreadStatus[] = $notiData['readStatus'];				
				$id[]   = $notiData['id'];
			}
				$count = count($notificationID);

			for($i = 0; $i<=$count -1; $i++){

		?> 
		  <li class="list-group-item">
  		  	<span class = "notification-head-unread"> <?php echo $notficationHead[$i]; ?></span>
			  <div class = "row notification-row">
			  	<div class = "col-md-12 notification-body">
			  		<?php echo "<pre>" . $notficationDetail[$i] . "</pre>"; ?>
			  	</div>
				<div class="btn-group pull-right">
				  <button type="button" class="btn btn-xs btn-success notificationStatusBtn" id = "<?php echo $notificationID[$i]; ?>" >Mark as a Read</button>				<span id="notifID<?php echo $id[$i]; ?>" style="display:none;" ><?php echo $id[$i]; ?></span>	
				</div>

			  </div>
		  </li>
		  <?php } ?>
<!--*******************************************************************************************-->
		</ul>
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