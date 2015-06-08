<?php
	require ("../data/connect.php");

	$idWr  = $_GET['idWr'];
	$operation = $_GET['operation'];

	if ($operation == "hc"){
	$query = mysql_query("SELECT * FROM hcfailing  where idWr = '$idWr' order by idHC ASC");

	echo '<tr>
			<th>id</th>
			<th>Exit Code</th>
			<th>Operation</th>
	  	  </tr>';

	while($data = mysql_fetch_row($query))
		{   
			echo '<tr>';
			echo '<td>'.$data[0].'</td>';
			echo '<td class="hcexitcode">'.$data[2].'</td>';
			echo '<td> <a class="btn btn-danger btn-xs hcremoveExitCode"> Remove </a></td></tr>';
		}
};


if ($operation == "sam"){
$query = mysql_query("SELECT * FROM samfailing  where idWr = '$idWr' order by idSAM ASC");

	echo '<tr>
			<th>id</th>
			<th>Exit Code</th>
			<th>Operation</th>
	  	  </tr>';

	while($data = mysql_fetch_row($query))
		{   
			echo '<tr>';
			echo '<td>'.$data[0].'</td>';
			echo '<td class="samexitcode">'.$data[2].'</td>';
			echo '<td> <a class="btn btn-danger btn-xs samremoveExitCode"> Remove </a></td></tr>';
		}	
};


if ($operation == "links"){
$query = mysql_query("SELECT * FROM linksfailing  where idWr = '$idWr' order by idLINKS ASC");

	echo '	
		<tr>
		    <th>id</th>
		    <th>Good<br>T2 from T1</th>
		    <th>Good<br>T2 to T1</th>
		    <th>Active<br>T2 from T1</th>
		    <th>Active<br>T2 to T1</th>
		    <th>Operation</th>
		</tr>';

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
};


?>
