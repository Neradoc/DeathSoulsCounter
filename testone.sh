#!/bin/sh

. header.sh
file=$1
res=$2
del=$3

if [[ -z $file ]]; then
	echo "NO TARGET"
	exit
fi
if [[ -z $res ]]; then res=720; fi

# résolution
MASKDIR="$res"
if [ "$res" = "360" ]; then
	# cropage
	cropDims="212x48+171+134"
	# nb dans le masque: 3741
	MINPIXELON=800
	# nb dans le masque: 6435
	MAXPIXELOFF=1000
fi
if [ "$res" = "720" ]; then
	# cropage
	cropDims="420x90+342+274"
	# nb dans le masque: 12801
	MINPIXELON=2300
	# nb dans le masque: 24999
	MAXPIXELOFF=2500
fi
if [ "$res" = "720fr" ]; then
	#cropage
	cropDims="694x84+204+284"
	# nb dans le masque: 12801
	MINPIXELON=2300
	# nb dans le masque: 24999
	MAXPIXELOFF=2500
fi

timestamp=`date +%s`
NAME=`basename $file`

# Sur chaque image rechercher le texte "YOU DIED"
# - croper la zone de l'écran qui doit le contenir
# x/y: 342x274 w/h: 420x90
# $ convert imgs/frames/out$x.png -crop 420x90+342+274 imgs/crops/out$x.png
convert "$file" -crop $cropDims "${file}.crop.png"

# - appliquer un masque pour ne garder que la zone du texte
# $ composite -compose Multiply out67c.png mask-off.png out67m.png
#DEBUG: composite -compose Multiply "${file}.crop.png" "$MASKDIR/mask-off.png" "${file}.mask.png"

# - appliquer un seuil pour ne garder que les pixels "assez rouges"
# - augmenter la saturation
# $ convert out67c.png -modulate 100,500 out67s.png
# - remplir de noir les couleurs pas proches du rouge
# $ convert out67s.png -fill Black -fuzz 25% +opaque Red out67fr.png
#DEBUG: convert "${file}.mask.png" -modulate 100,500 "${file}.red.png"
#DEBUG: convert "${file}.red.png" -fill Black -fuzz 25% +opaque Red "${file}.red.png"

# - compter le nombre de pixels
#DEBUG: PIXELON=`convert "${file}.red.png" \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`

PIXELON=`convert -compose Multiply "$MASKDIR/mask-off.png" "${file}.crop.png" -composite -modulate 100,500 -fill Black -fuzz 25% +opaque Red \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`

printf "PIXELON : %6d  " $PIXELON

# Tester si tout l'écran est rouge:
# - faire un masque pour la zone autour des mots "YOU DIED"
#DEBUG: composite -compose Multiply "${file}.crop.png" "$MASKDIR/mask-on.png" "${file}.maskx.png"
# - appliquer un seuil pour ne garder que les pixels "assez rouges"
#DEBUG: convert "${file}.maskx.png" -modulate 100,500 "${file}.redx.png"
#DEBUG: convert "${file}.redx.png" -fill Black -fuzz 25% +opaque Red "${file}.redx.png"

# - compter le nombre de pixels
#DEBUG: PIXELOFF=`convert "${file}.redx.png" \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`
PIXELOFF=`convert -compose Multiply "$MASKDIR/mask-on.png" "${file}.crop.png" -composite -modulate 100,500 -fill Black -fuzz 25% +opaque Red \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`

printf "PIXELOFF: %6d  " $PIXELOFF

# - comparer le taux de rouge à celui de la zone des mots
# (il doit en effet y avoir un masque noir autour des mots)
if ((PIXELON < MINPIXELON || PIXELOFF > MAXPIXELOFF)); then
	printf "FALSE: "
else
	# - copier l'image d'origine dans le dossier des morts trouvées
	printf "FOUND: "
fi
echo $NAME

endtimes=`date +%s`
if [[ ! -z $del ]]; then
	rm ${file}.*.png
fi
#echo "\n============ "$((endtimes-timestamp))" s ============"
