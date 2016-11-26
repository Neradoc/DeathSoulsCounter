<?php
include("keyfile.php");

if(isset($_REQUEST['nmorts'])) {
	$nombreDeMorts = count(glob("deaths/death_*.jpg")) + count(glob("compteur/death_*.jpg"));
	print($nombreDeMorts);
	exit();
}
if(isset($_REQUEST['screen'])) {
	if( file_exists("display/compteur.jpg") ) {
		print("display/compteur.jpg");
		exit();
	}
	$files = glob("compteur/death_*.jpg");
	if(count($files) == 0) {
		$files = glob("deaths/death_*.jpg");
	}
	if(count($files) == 0) {
		print("");
	} else {
		natcasesort($files);
		print(end($files));
	}
	exit();
}
if(isset($_FILES['file'])) {
	$filename = preg_replace('`[^a-zA-Z0-9._-]`','',$_FILES["file"]["name"]);
	if( ! preg_match('/\.jpg$/',$filename,$m) ) {
		print("NO VALID FILE NAME");
		exit();
	}
	if(hash_hmac("sha1",$filename,$magickey) != $_POST['filecode']) {
		print("INVALID SIGNATURE");
		exit();
	}
	if(! file_exists($_FILES["file"]["tmp_name"])) {
		print("NO VALID FILE");
		exit();
	}
	if(filesize($_FILES["file"]["tmp_name"]) > 1024*1024*0.5) {
		print("FILE TOO BIG");
		exit();
	}
	$target_dir = "compteur/";
	$target_file = $target_dir . $filename;
	move_uploaded_file($_FILES["file"]["tmp_name"], $target_file);
	if($_POST['remplace']) {
		$replace = preg_replace('`[^a-zA-Z0-9._-]`','',$_POST['remplace']);
		if(file_exists($target_dir.$replace)) {
			unlink($target_dir.$replace);
		}
	}
	print("OK $target_file");
	exit();
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
	<meta charset="utf-8" />
	<title>Il est mort ! Il est mort ! Il est mort !</title>
	<style type="text/css" title="text/css">
		/* vos styles ici */
		@font-face {
			font-family: DarkSouls;
			src:url(OptimusPrincepsSemiBold.ttf);
		}
		body {
			font-family: "DarkSouls, Comic Sans MS";
		}
		#contenu {
			width: 300px;
			/* border: 4px solid #BBB; */
			/* border-radius: 20px; */
		}
		#compteur
		{
			color: #C00000;
			font-weight: bold;
			font-size: 80px;
			width: 280;
			padding: 8px;
			margin: auto;
			text-align: center;
			background-image: url(img/fondiffus-darksouls.png);
			background-repeat: no-repeat;
			background-position: center center;
		}
		#screen {
			text-align: center;
		}
		#screen a {
			text-decoration: none;
		}
		#screen img {
			max-width: 300px;
			/* border-radius: 0px 0px 20px 20px; */
		}
	</style>
	<script type="text/javascript" src="jq/v2.js"></script>
	<script type="text/javascript" language="javascript" charset="utf-8">
		/* votre code ici */
		function update_morts() {
			$("#compteur").load("compteur.php", {nmorts:"1"});
		}
		function update_image() {
			$.ajax({
				url:'compteur.php',
				type:'POST',
				data: {
					screen: 1
				},
				success: function(data,status){
					if(data == "") {
						data = "img/default_back.jpg";
					}
					$("#screen a").attr("href",data);
					$("#screen img").attr("src",data);
				}
			});
		}
		$(function() {
			setInterval(update_morts,1000);
			setInterval(update_image,1000);
		});
	</script>
</head>
<body>
<div id="contenu">
	<div id="compteur"><img src="img/loading-activity.gif"/></div>
	<div id="screen"><a href="" target="_blank"><img src="img/default_back.jpg" /></a></div>
</div>
</body>
</html>
