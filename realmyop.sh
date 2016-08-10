#!/bin/sh

source header.sh

if [[! -z $1 ]]; then
	DIR="$1"
fi
if (($1 == "-")); then
	DIR="$1"
fi
echo "UTILISATION DE $DIR"

mkdir -p $DIR/imgs
mkdir -p $DIR/imgs/crops
mkdir -p $DIR/imgs/frames
mkdir -p $DIR/imgs/mask
mkdir -p $DIR/imgs/reds
mkdir -p $DIR/imgs/maskx
mkdir -p $DIR/imgs/redx
mkdir -p $DIR/found

# convertir les videos en segments
## ffmpeg -i videos/darksouls2.mp4 -map 0 -c copy -f segment -segment_time 60 -reset_timestamps 1 segments/vid_02_%08d.mp4
## ffmpeg -i videos/darksouls3.mp4 -map 0 -c copy -f segment -segment_time 60 -reset_timestamps 1 segments/vid_03_%08d.mp4

# Extraire des images de la vidéo. Par exemple 2 images par seconde.
# résolution
case $2 in
	360 )
		res=360
		;;
	720 )
		res=720
		;;
	* )
		res=720
		;;
esac
MASKDIR="$res"
if ((res == 720)); then
	# nb dans le masque: 12801
	MINPIXELON=2300
	# nb dans le masque: 24999
	MAXPIXELOFF=2500
fi
if ((res == 360)); then
	# nb dans le masque: 3741
	MINPIXELON=800
	# nb dans le masque: 6435
	MAXPIXELOFF=1000
fi
# numéro de la vidéo (%02d)
videoNum="04"
# passer combien de vidéos au début
startat=5
# etc.
vid=0
skip=0
for segment in $DIR/segments/vid_${videoNum}_*.mp4; do
	vid=$((vid+1))
	if ((vid < startat+1)); then
		continue
	fi
	timestamp=`date +%s`
	# supprimer les fichiers du dossier d'images
	rm -rf $DIR/imgs/*
	mkdir -p $DIR/imgs/crops
	mkdir -p $DIR/imgs/frames
	mkdir -p $DIR/imgs/mask
	mkdir -p $DIR/imgs/reds
	mkdir -p $DIR/imgs/maskx
	mkdir -p $DIR/imgs/redx
	# créer les images de ce segment
	nvid=`printf "%04d" $((vid-1))`
	ffmpeg -i "$segment" -vf fps=$FPS "$DIR/imgs/frames/death_${videoNum}_${nvid}_%04d.png"
	
	echo "============ "`basename $segment`" || ($nvid) ============"
	echo "============ "`date`
	
	for file in $DIR/imgs/frames/*; do
		# skipper les frames à skipper
		if ((skip > 0)); then
			((skip -= 1))
			continue
		fi
		
		NAME=`basename $file`
		# Sur chaque image rechercher le texte "YOU DIED"
		# - croper la zone de l'écran qui doit le contenir
		# x/y: 342x274 w/h: 420x90
		# $ convert imgs/frames/out$x.png -crop 420x90+342+274 imgs/crops/out$x.png
		if ((res == 360)); then
			convert "$file" -crop 212x48+171+134 "$DIR/imgs/crops/$NAME"
		fi
		if ((res == 720)); then
			convert "$file" -crop 420x90+342+274 "$DIR/imgs/crops/$NAME"
		fi
	
		# - appliquer un masque pour ne garder que la zone du texte
		# $ composite -compose Multiply out67c.png mask-off.png out67m.png
		composite -compose Multiply "$DIR/imgs/crops/$NAME" "$MASKDIR/mask-off.png" "$DIR/imgs/mask/$NAME"

		# - appliquer un seuil pour ne garder que les pixels "assez rouges"
		# - augmenter la saturation
		# $ convert out67c.png -modulate 100,500 out67s.png
		# - remplir de noir les couleurs pas proches du rouge
		# $ convert out67s.png -fill Black -fuzz 25% +opaque Red out67fr.png
		convert "$DIR/imgs/mask/$NAME" -modulate 100,500 "$DIR/imgs/reds/$NAME"
		convert "$DIR/imgs/reds/$NAME" -fill Black -fuzz 25% +opaque Red "$DIR/imgs/reds/$NAME"

		# - compter le nombre de pixels
		PIXELON=`convert "$DIR/imgs/reds/$NAME" \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`
		
		printf "."
		if ((PIXELON > 0)); then
			printf "%04d" $PIXELON
		fi
		
		# - comparer à un seuil
		# Si c'est bon
		if ((PIXELON > MINPIXELON)); then

			# Tester si tout l'écran est rouge:
			# - faire un masque pour la zone autour des mots "YOU DIED"
			composite -compose Multiply "$DIR/imgs/crops/$NAME" "$MASKDIR/mask-on.png" "$DIR/imgs/maskx/$NAME"
			# - appliquer un seuil pour ne garder que les pixels "assez rouges"
			convert "$DIR/imgs/maskx/$NAME" -modulate 100,500 "$DIR/imgs/redx/$NAME"
			convert "$DIR/imgs/redx/$NAME" -fill Black -fuzz 25% +opaque Red "$DIR/imgs/redx/$NAME"

			# - compter le nombre de pixels
			PIXELOFF=`convert "$DIR/imgs/redx/$NAME" \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`
		
			# - comparer le taux de rouge à celui de la zone des mots
			# (il doit en effet y avoir un masque noir autour des mots)
			if ((PIXELOFF > MAXPIXELOFF)); then
				cp "$file" "$DIR/false/$NAME"
			else
				printf ".\n"
				echo "___________________________________________________"
				echo "$PIXELON in $NAME from $segment"
				echo "$PIXELON in $NAME from $segment" >> "$DIR/found_liste.txt"
				# - copier l'image d'origine dans le dossier des morts trouvées
				cp "$file" "$DIR/found/$NAME"
				# - sauter quelques images (5-10 secondes)
				((skip = 2*FPS))
			fi
		fi
		endtimes=`date +%s`
	done
	echo "\n============ "$((endtimes-timestamp))" s ============"
done
