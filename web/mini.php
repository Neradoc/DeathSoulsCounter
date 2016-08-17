<?php

function make_small($dir,$file,$force=false,$size=80) {
	// normaliser $dir
	$dir = preg_replace('{/+$}','/',$dir.'/');
	if(preg_match(',([^/]+)\.([^./]+)$,i',$file,$matches)) {
		$name=$matches[1];
		#$ext=".".$matches[2];
	} else {
		$name=basename($file);
		#$ext=".jpg";
	}
	$name = md5($file)."-".$name;
	// pour commencer le fichier existe-t-il ?
	if( !file_exists($file) ) {
		return false;
	}
	// la miniature existe t elle déjà ?
	if( file_exists($dir.$name.".$size.jpg") ) {
		if($force) {
			# effacer (unlink) le fichier
			unlink($dir.$name.".$size.jpg");
		} else {
			return $dir.$name.".$size.jpg";
		}
	}
	// il y a un fichier et il n'y a pas (ou plus) de miniature
	// prendre $file.".jpg"
	$src_im = imagecreatefromjpeg($file);
	// réduire son plus grand coté à $size (et l'autre proportionnellement)
	$W = imagesx($src_im);
	$H = imagesy($src_im);
	if( $W > $H ) {
		$dst_im = imagecreatetruecolor($size, floor( $H * $size / $W ));
	} else {
		$dst_im = imagecreatetruecolor(floor( $W * $size / $H ), $size);
	}
	// print( "<h1>".imagesx($dst_im)." -- ".imagesy($dst_im)."</h1>" );
	imagecopyresampled($dst_im,$src_im,0,0,0,0,imagesx($dst_im),imagesy($dst_im),$W,$H);
	// mettre le résultat dans $file.".$size.jpg" en bonne qualité
	imagejpeg($dst_im, $dir.$name.".$size.jpg");
	//
	return $dir.$name.".$size.jpg";
}

function send_small($dir,$file,$force=false,$size=80) {
	$mime = array(
		"jpg" => "image/jpeg",
		"gif" => "image/gif",
		"png" => "image/png",
	);
	$imagePath =  make_small($dir,$file,$force,$size);
	if (preg_match(',^.+\.(gif|jpg|png)$,i', $imagePath, $r) AND @file_exists($imagePath)){
		ob_end_clean();
		header('Content-Type: '.$mime[strtolower($r[1])]);
		header('Content-Length: '.filesize($imagePath));
		readfile($imagePath);
		exit(0);
	}
}

if(isset($_GET['img'])) {
	ob_start();
	$size = 180;
	if(isset($_GET['size'])) {
		$size = intval($_GET['size']);
	}
	if($size <= 1 || $size > 2000) {
		$size = 180;
	}
	$dir = __DIR__;
	$fileIn = preg_replace('`//+`',"/",$dir."/".$_GET['img']);
	$fileIn = preg_replace('`\.\./`',"",$fileIn);
	send_small($dir."/miniatures/",$fileIn,false,$size);
}
