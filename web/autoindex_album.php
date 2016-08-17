<!DOCTYPE html>
<?php
setlocale(LC_ALL,"fr_FR.utf8");
include("mini.php");

if(!isset($TARGET_DIR)) $TARGET_DIR = dirname($_SERVER['SCRIPT_FILENAME']);
if(!isset($TARGET_URL)) $TARGET_URL = "";
if(!isset($DISP_PHP)) $DISP_PHP = false;
if(!isset($DISP_HTML)) $DISP_HTML = false;
if(!isset($MINIATURES)) $MINIATURES = false;
if(!isset($TRANSFORME_NOMS)) $TRANSFORME_NOMS = false;
if(!isset($REMOVE_PREFIX)) $REMOVE_PREFIX = false;
if(!isset($EBOOKS)) $EBOOKS = true;
if(!isset($TITRE)) $TITRE = $_SERVER["REQUEST_URI"];
$files = glob(preg_replace("`//+`","/",$TARGET_DIR."/*"));

// CONFIG taille des miniatures
$mini_size = "180";

/**
 * Return human readable sizes
 *
 * @author      Aidan Lister <aidan@php.net>
 * @version     1.3.0
 * @link        http://aidanlister.com/2004/04/human-readable-file-sizes/
 * @param       int     $size        size in bytes
 * @param       string  $max         maximum unit
 * @param       string  $system      'si' for SI, 'bi' for binary prefixes
 * @param       string  $retstring   return string format
 */
function size_readable($size, $max = null, $system = 'si', $retstring = '%01.2f %s')
{
    // Pick units
    $systems['si']['prefix'] = array('o', 'ko', 'Mo', 'Go', 'To', 'Po');
    $systems['si']['size']   = 1000;
    $systems['bi']['prefix'] = array('o', 'Kio', 'Mio', 'Gio', 'Tio', 'PiB');
    $systems['bi']['size']   = 1024;
    $sys = isset($systems[$system]) ? $systems[$system] : $systems['si'];

    // Max unit to display
    $depth = count($sys['prefix']) - 1;
    if ($max && false !== $d = array_search($max, $sys['prefix'])) {
        $depth = $d;
    }

    // Loop
    $i = 0;
    while ($size >= $sys['size'] && $i < $depth) {
        $size /= $sys['size'];
        $i++;
    }

    return sprintf($retstring, $size, $sys['prefix'][$i]);
}
//
function serverUrl() {
	$serverUrl = 'http';
	if (@$_SERVER["HTTPS"] == "on") {$serverUrl .= "s";}
	$serverUrl .= "://".$_SERVER["SERVER_NAME"];
	if ($_SERVER["SERVER_PORT"] != "80") {
		$serverUrl .= ":".$_SERVER["SERVER_PORT"];
	}
	return $serverUrl;
}
function curPageUrl() {
	return serverUrl().$_SERVER["REQUEST_URI"];
}
function baseUrl() {
	$server_url = serverUrl();
	$script_url = dirname($_SERVER['SCRIPT_NAME']);
	if($script_url != '/') $script_url .= '/';
	$url = $server_url.$script_url;
	return $url;
}
?>
<html lang="fr">
<head>
	<title><?php echo $TITRE ?></title>
	<meta http-equiv="content-type" content="text/html; charset=utf-8">
	<script src="~jq/v1.js" type="text/javascript" language="javascript"></script>
	<link rel="stylesheet" href="~jq/jsbox/jsbox.css" />
	<script src="jq/jsbox/jsbox.js" type="text/javascript" language="javascript"></script>
	<?php if($TARGET_URL) print('<base href="'.$TARGET_URL.'"/>'); ?>
	<script type="text/javascript">
	<!--
	function disp_visible(that) {
		var scroll = $(document).scrollTop();
		var height = $(window).height();
		var top = $(that).offset().top - scroll;
		var bottom = top + $(that).outerHeight();
		if(top>0 && top<height || bottom>0 && bottom<height) {
			var img = $(that).data('link');
			if(img) {
				$(that).removeClass("notini");
				$(that).attr('src', "img/gris-load-90.gif");
				var image = new Image();
				image.onload = function() {
					$(that).attr('src',img).css({
						width: "auto",
						//maxWidth: "120px",
						height: "auto",
						//maxHeight: "90px",
					});
				};
				image.src = img;
			}
		}
	}
	var disp_visibles = function() {
		$(".notini").each(function(){ disp_visible(this); });
	}
	$(document).ready(function() {
		var targets = 'a.navigue';
		$(targets).jsbox();
		//
		disp_visibles();
		$(window).resize(disp_visibles);
		$(window).scroll(disp_visibles);
	});
	//-->
	</script>
	<style type="text/css">
		.mini {
			 width:<?php echo $mini_size; ?>px;
			 height:<?php echo $mini_size; ?>px;
		}
		td {
			padding: 2px 5px;
			border-right: 1px dashed #BBB;
			border-bottom: 1px solid #BBB;
		}
		td.col_mini {
			 width:<?php echo $mini_size; ?>px;
			 height:<?php echo $mini_size; ?>px;
			 text-align:center;
			 vertical-align:middle;
		}
		.lien_direct {
			font-size: 90%;
			color: #888;
			background: #EEE;
		}
	</style>
</head>
<body>
<h1><?php echo $TITRE ?></h1>
<!-- <div><a href="..">remonter</a></div> -->
<table>
<?php
$i = 0;
$ncase = 0;
foreach($files as $file):
	$i++;
	$href = basename($file);
	$href_abs = baseUrl().$href;
	$img = $href;
	$is_ebook = false;
	if($MINIATURES) {
		$path = str_replace(__DIR__."/","",$file);
		$img = "mini.php?size=$mini_size&img=$path";
	}
	if($file == $_SERVER['SCRIPT_FILENAME']) continue;
	if(!$DISP_PHP && substr($file,-4,4)==".php") continue;
	if(!$DISP_HTML && substr($file,-5,5)==".html") continue;
	if(!$DISP_HTML && substr($file,-4,4)==".htm") continue;
	if($EBOOKS && substr($file,-5,5)==".epub") {
		$hbook = $href; // preg_replace(',^[a-z]+://,','ereader://',$href_abs);
		$is_ebook = true;
	}
	$title = $href;
	if($TRANSFORME_NOMS) {
		$title = preg_replace('/\.(jpg|png|gif|jpeg)$/i','',$title);
		$title = preg_replace('/[-_]/',' ',$title);
		$dd = preg_replace('/[^a-z0-9]/i','',basename($TARGET_DIR));
		$title = preg_replace('/^'.$dd.' /i','',$title);
		if($REMOVE_PREFIX) {
			$REMOVE_PREFIX = preg_replace('/[^a-z0-9]/i','',$REMOVE_PREFIX);
			$title = preg_replace('/^'.$REMOVE_PREFIX.' /i','',$title);
		}
		$title = ucwords($title);
	}
	//
	$is_pdf = preg_match('/\.pdf$/i',$file);
	$is_image = preg_match('/\.(jpg|jpeg|gif|png)$/i',$file);
	$is_display = $is_image || preg_match('/\.(ico)$/i',$file);
	?>
	<?php if($is_display): ?>
	<?php if($ncase %5 == 0): ?>
	<tr>
	<?php endif; ?>
		<td class="col1 col_mini">
			<a id="a_num_<?php echo $i ?>" href="<?php echo $href ?>" class="navigue" rel="galerie" title="<?php echo $href ?>"><img class="mini notini" src="img/gris.png" data-link="<?php echo $img ?>" /></a><br/>
			<a data-num="<?php echo $i ?>" href="<?php echo $href ?>" onclick="$('#a_num_'+$(this).data('num')).click(); return false;"><?php echo $title ?></a>
		</td>
	<?php if($ncase %5 == 4): ?>
	</tr>
	<?php endif; ?>
	<?php
	$ncase++;
	endif; ?>
<?php
endforeach; ?>
</table>
</body>
</html>