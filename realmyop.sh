#!/bin/sh

source header.sh

# passer combien de vidéos au début
startAt=0
# numéro du premier segment (pour coller aux numéros réels)
vid=0

while getopts ":s:v:" opt; do
	case $opt in
		s)
			startAt="$OPTARG"
			;;
		v)
			vid="$OPTARG"
			;;
		\?)
			echo "Invalid option -$OPTARG" >&2
			exit
			;;
		:)
			echo "Option -$OPTARG requires an argument." >&2
			exit
			;;
	esac
done
shift $((OPTIND-1))

ARGUMENTSLIST='Arguments: [-s <startAt>] [-v <startVid>] <DIR> <videoNum> <res>'"\n
startAt: nombre de segments à sauter au début (pour relancer par ex)\n
startVid: numéro du premier segment (si on en a supprimé 5, mettre 5)\n
DIR: dossier racine des données (contient 'segments/' et 'found/')\n
videoNum: numéro de la VOD\n
res: résolution/format de masque (360, 720, 720fr)"

# dossier utilisé
if [[ ! -z "$1" ]]; then
	if [[ "$1" = "-" ]]; then
		DIR=$DIR_BASE
	else
		DIR="$1"
	fi
else
	echo $ARGUMENTSLIST
	exit
fi
echo "UTILISATION DE $DIR"

# numéro de la vidéo (%02d)
if [[ ! -z "$2" ]]; then
	videoNum="$2"
else
	echo $ARGUMENTSLIST
	exit
fi

# format des images et masques
case "$3" in
	360 )
		res=360
		;;
	720 )
		res=720
		;;
	720fr )
		res=720fr
		;;
	* )
		echo $ARGUMENTSLIST
		exit
		;;
esac

# dossier des images
IMGDIR="imgs"
FOUND="found"
FOUND_TIMED="${FOUND}_0_timed"

mkdir -p $DIR/$IMGDIR
mkdir -p $DIR/$IMGDIR/crops
mkdir -p $DIR/$IMGDIR/frames
mkdir -p $DIR/$FOUND
mkdir -p $DIR/$FOUND_TIMED

# convertir les videos en segments
## ffmpeg -i videos/darksouls3.mp4 -map 0 -c copy -f segment -segment_time 60 -reset_timestamps 1 segments/vid_03_%08d.mp4

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
# etc.
Folse=0
skip=0
echo "VIDEONUM $videoNum - START AT $startAt - VID $vid"
for segment in $DIR/segments/vid_${videoNum}_*.mp4; do
	vid=$((vid+1))
	if ((vid < startAt+1)); then
		continue
	fi
	timestamp=`date +%s`
	# supprimer les fichiers du dossier d'images
	for del in $DIR/$IMGDIR/*/death_${videoNum}_*; do
		rm "$del"
	done
	# Extraire des images de la vidéo. Par exemple 5 images par seconde.
	# créer les images de ce segment -ss -t
	nvid=`printf "%04d" $((vid-1))`
	ffmpeg -i "$segment" -vf fps=$FPS "$DIR/$IMGDIR/frames/death_${videoNum}_${nvid}_%04d.png"
	
	echo "============ "`basename $segment`" || ($nvid) ============"
	echo "============ "`date`
	
	frameNum=-1
	for file in $DIR/$IMGDIR/frames/death_${videoNum}_${nvid}_*; do
		((frameNum = frameNum + 1))
		# skipper les frames à skipper
		if ((skip > 0)); then
			((skip -= 1))
			continue
		fi
		
		NAME=`basename $file`
		# Sur chaque image rechercher le texte "YOU DIED"
		# - croper la zone de l'écran qui doit le contenir
		# x/y: 342x274 w/h: 420x90
		# $ convert $IMGDIR/frames/out$x.png -crop 420x90+342+274 $IMGDIR/crops/out$x.png
		convert "$file" -crop $cropDims "$DIR/$IMGDIR/crops/$NAME"
	
		# - appliquer un masque pour ne garder que la zone du texte
		# $ composite -compose Multiply out67c.png mask-off.png out67m.png
		# - appliquer un seuil pour ne garder que les pixels "assez rouges"
		# - augmenter la saturation
		# $ convert out67c.png -modulate 100,500 out67s.png
		# - remplir de noir les couleurs pas proches du rouge
		# $ convert out67s.png -fill Black -fuzz 25% +opaque Red out67fr.png
		# - compter le nombre de pixels
		
		PIXELON=`convert -compose Multiply "$MASKDIR/mask-off.png" "$DIR/$IMGDIR/crops/$NAME" -composite -modulate 100,500 -fill Black -fuzz 25% +opaque Red \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`
		
		printf "."
		if ((PIXELON > 0)); then
			printf "%04d" $PIXELON
		fi
		
		# - comparer à un seuil
		# Si c'est bon
		if ((PIXELON > MINPIXELON)); then

			# Tester si tout l'écran est rouge:
			# - faire un masque pour la zone autour des mots "YOU DIED"
			# - appliquer un seuil pour ne garder que les pixels "assez rouges"
			# - compter le nombre de pixels
			PIXELOFF=`convert -compose Multiply "$MASKDIR/mask-on.png" "$DIR/$IMGDIR/crops/$NAME" -composite -modulate 100,500 -fill Black -fuzz 25% +opaque Red \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:`
		
			# - comparer le taux de rouge à celui de la zone des mots
			# (il doit en effet y avoir un masque noir autour des mots)
			if ((PIXELOFF > MAXPIXELOFF)); then
				((Folse = Folse + 1))
			else
				printf "\n"
				echo "___________________________________________________"
				echo "$PIXELON in $NAME from $segment"
				echo "$PIXELON in $NAME from $segment" >> "$DIR/found_liste.txt"
				# - copier l'image d'origine dans le dossier des morts trouvées
				cp "$file" "$DIR/$FOUND/$NAME"
				# - le renommage
				((minutes = (vid - 1 + frameNum/300) % 60))
				((seconds = (frameNum/5) % 60))
				((heures = (vid - 1 + frameNum/300) / 60))
				fname=`printf "death_%s_%dh%02dm%02ds.png" "$videoNum" "$heures" "$minutes" "$seconds"`
				cp "$file" "$DIR/$FOUND_TIMED/$fname"
				# - sauter quelques images (5-10 secondes)
				((skip = 2*FPS))
			fi
		fi
		endtimes=`date +%s`
	done
	echo "\n============ "$((endtimes-timestamp))" s ============"
done
