#!/bin/sh

DIR="/Users/spyro/_exclus_de_timemachine/realmyop"
FPS=5

mkdir -p $DIR/imgs
mkdir -p $DIR/imgs/crops
mkdir -p $DIR/imgs/frames
mkdir -p $DIR/imgs/mask
mkdir -p $DIR/imgs/reds

mkdir -p $DIR/found

# convertir les videos en segments
## ffmpeg -i videos/darksouls2.mp4 -map 0 -c copy -f segment -segment_time 120 -reset_timestamps 1 segments/vid_2_%08d.mp4

# Extraire des images de la vidéo. Par exemple 2 images par seconde.
vid=0
skip=0
startat=5
for segment in $DIR/segments/*.mp4; do
	vid=$((vid+1))
	if ((vid < startat)); then
		continue
	fi
	# supprimer les fichiers du dossier d'images
	rm -rf $DIR/imgs/*/*.png
	# créer les images de ce segment
	ffmpeg -i "$segment" -vf fps=$FPS "$DIR/imgs/frames/out_${vid}_%08d.png"
	
	echo "============ $segment ============"
	
	for file in $DIR/imgs/frames/*; do
		# skipper les frames à skipper
		if ((skip > 0)); then
			((skip -= 1))
			continue
		fi
		
		NAME=`basename $file`
		# Sur chaque image rechercher le texte "YOU ARE DEAD"
		# - croper la zone de l'écran qui doit le contenir
		# x/y: 342x274 w/h: 420x90
		# $ convert imgs/frames/out$x.png -crop 420x90+342+274 imgs/crops/out$x.png
		convert "$file" -crop 420x90+342+274 "$DIR/imgs/crops/$NAME"
	
		# - appliquer un masque pour ne garder que la zone du texte
		# $ composite -compose Multiply out67c.png mask-off.png out67m.png
		composite -compose Multiply "$DIR/imgs/crops/$NAME" "mask-off.png" "$DIR/imgs/mask/$NAME"

		# - appliquer un seuil pour ne garder que les pixels "assez rouges"
		# - augmenter la saturation
		# $ convert out67c.png -modulate 100,500 out67s.png
		# - remplir de noir les couleurs pas proches du rouge
		# $ convert out67s.png -fill Black -fuzz 25% +opaque Red out67fr.png
		convert "$DIR/imgs/mask/$NAME" -modulate 100,500 "$DIR/imgs/reds/$NAME"
		convert "$DIR/imgs/reds/$NAME" -fill Black -fuzz 25% +opaque Red "$DIR/imgs/reds/$NAME"

		# - compter le nombre de pixels
		RESULT=`convert "$DIR/imgs/reds/$NAME" \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`

		# Si l'écran est rouge:
		# - faire un masque pour la zone autour des mots "YOU ARE DEAD"
		# - comparer le taux de rouge à celui de la zone des mots
		# (il doit en effet y avoir un masque noir autour des mots)
		
		printf "."
		
		# - comparer à un seuil
		# Si c'est bon
		if ((RESULT > 2500)); then
			printf ".\n"
			echo "___________________________________________________"
			echo "$RESULT in $NAME from $segment"
			# - copier l'image d'origine dans le dossier des morts trouvées
			cp "$file" "$DIR/found/$NAME"
			# - sauter quelques images (5-10 secondes)
			((skip = 2*FPS))
		fi
	done
done