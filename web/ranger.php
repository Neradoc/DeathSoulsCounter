<pre><?php
# aller chercher les fichiers dans compteur
# convertir le format des noms si nécessaire
# déplacer dans deaths
$images = glob("compteur/death_*.jpg");

for($images as $image) {
	$nom = basename($image);
	if(preg_match('/(death_.*_)(\d+\.\d)\.jpg/',$m)) {
		$heures = floor($m[2]/60/60);
		$minutes = floor($m[2]/60 % 60);
		$secondes = floor($m[2]) % 60;
		$stamp=sprintf("%dh%02dm%02ds", $heures, $minutes, $secondes);
		$nouveau = $m[1].$stamp.".jpg";
	} else {
		$nouveau = $nom;
	}
	# rename($image,"deaths/".$nouveau);
	print("rename(\"$image\",\"deaths/$nouveau\");\n");
}

/*
ls death_12_*.jpg | perl -ne 's/\n//; $n=$_; s/x/0/; m/(\d+\.\d)/; $h=$1/60/60; $m=$1/60%60; $s=$1%60; $stamp=sprintf("%dh%02dm%02ds", $h, $m, $s); s/\d+\.\d/$stamp/; print("mv $n $_\n");'
*/
