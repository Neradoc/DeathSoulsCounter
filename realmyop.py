#!/usr/bin/env python

import glob

data_dir = "/Users/spyro/_exclus_de_timemachine/realmyop/"
video_files = glob.glob(data_dir+"videos/*")

print(video_files)

video_files = [ data_dir+"videos/test.mp4" ]
for video in video_files:
	pass

"""
Extraire des images de la vidéo. Par exemple 2 images par seconde.
$ ffmpeg -i videos/test.mp4 -vf fps=5 imgs/frames/out%d.png 

Sur chaque image rechercher le texte "YOU ARE DEAD"
- croper la zone de l'écran qui doit le contenir
x/y: 342x274 w/h: 420x90
$ convert imgs/frames/out$x.png -crop 420x90+342+274 imgs/crops/out$x.png
$ for file in imgs/frames/*; do convert "$file" -crop 420x90+342+274 "imgs/crops/"`basename $file`; done

- appliquer un masque pour ne garder que la zone du texte
$ composite -compose Multiply out67c.png mask-off.png out67m.png
$ for file in imgs/crops/*; do composite -compose Multiply "$file" mask-off.png "imgs/mask/"`basename $file`; done

- appliquer un seuil pour ne garder que les pixels "assez rouges"
- augmenter la saturation
$ convert out67c.png -modulate 100,500 out67s.png
- remplir de noir les couleurs pas proches du rouge
$ convert out67s.png -fill Black -fuzz 25% +opaque Red out67fr.png

$ for file in imgs/mask/*; do convert "$file" -modulate 100,500 "imgs/reds/"`basename $file`; convert "imgs/reds/"`basename $file` -fill Black -fuzz 25% +opaque Red "imgs/reds/"`basename $file`; done

- compter le nombre de pixels
$ for file in imgs/reds/*; do convert "$file" \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:; echo; done


- comparer à un seuil

Si l'écran est rouge:
- faire un masque pour la zone autour des mots "YOU ARE DEAD"
- comparer le taux de rouge à celui de la zone des mots
(il doit en effet y avoir un masque noir autour des mots)

Si c'est bon
- copier l'image d'origine dans le dossier des morts trouvées
- sauter quelques images (5-10 secondes)
"""
