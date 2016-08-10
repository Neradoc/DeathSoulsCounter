#!/bin/sh

MASKDIR="."
DIR="/Users/spyro/_exclus_de_timemachine/realmyop"
FPS=5

mkdir -p $DIR/imgs
mkdir -p $DIR/imgs/crops
mkdir -p $DIR/imgs/frames
mkdir -p $DIR/imgs/mask
mkdir -p $DIR/imgs/reds
mkdir -p $DIR/imgs/maskx
mkdir -p $DIR/imgs/redx
mkdir -p $DIR/found

# convertir les videos en segments
## ffmpeg -i videos/darksouls2.mp4 -map 0 -c copy -f segment -segment_time 60 -reset_timestamps 1 segments/vid_2_%08d.mp4

# Extraire des images de la vidéo. Par exemple 2 images par seconde.
videoNum="03"
vid=0
startat=0
skipatstart=((startat+vid))
skip=0
for segment in $DIR/segments/vid${videoNum}_*.mp4; do
	vid=$((vid+1))
	if ((vid < skipatstart)); then
		continue
	fi
	# supprimer les fichiers du dossier d'images
	rm -rf $DIR/imgs/*
	mkdir -p $DIR/imgs
	mkdir -p $DIR/imgs/crops
	mkdir -p $DIR/imgs/frames
	mkdir -p $DIR/imgs/mask
	mkdir -p $DIR/imgs/reds
	mkdir -p $DIR/imgs/maskx
	mkdir -p $DIR/imgs/redx
	mkdir -p $DIR/found
	# créer les images de ce segment
	nvid=`printf "%04d" $vid`
	ffmpeg -i "$segment" -vf fps=$FPS "$DIR/imgs/frames/death_${videoNum}_${nvid}_%04d.png"
	
	echo "============ "`basename $segment`" ||||| ($nvid) ============"
	
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
		convert "$file" -crop 420x90+342+274 "$DIR/imgs/crops/$NAME"
	
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
		
		# - comparer à un seuil
		# Si c'est bon
		if ((PIXELON > 2300)); then

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
			if ((PIXELOFF > 2500)); then
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
	done
done
