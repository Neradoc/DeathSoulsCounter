<!DOCTYPE html>
<html lang="fr">
<head>
	<meta charset="utf-8" />
	<title>Pr&eacute;paire tou daille</title>
	<style type="text/css" title="text/css">
		.contenu {
			width: 800px;
			margin: auto;
			padding: 8px 16px;
			border: 2px solid #888;
			border-radius: 20px;
		}
		p {
			margin-bottom: 2px;
		}
		ul {
			padding: 0px;
			margin: 0px 0px 0px 20px;
		}
		li {
		}
		code {
			color: #008;
		}
	</style>
<!-- 
	<script type="text/javascript" src="jq/v2.js"></script>
	<script type="text/javascript" language="javascript" charset="utf-8">
		/* votre code ici */
	</script>
 -->
</head>
<body>
<div class="contenu">
<h1><a href="compteur.php">Le compteur interractif</a></h1>
<h1><a href=".">Toutes les morts trouvées par le script</a></h1>
<h2>Comment ça marche</h2>
<h3>Isoler les images à tester</h3>
<p>On commence avec un vidéo youtube gentiment téléchargée en 720p sur son ordinateur en quelques secondes grace à sa connection par la fibre (hin hin).</p>

<p>La vidéo est ensuite découpé en segments d'une minute environ (elle est coupée sur les keyframes donc ce n'est pas forcément exactement une minute).</p>

<p><code>ffmpeg -i darksoulsVOD_01.mp4 -map 0 -c copy -f segment -segment_time 60 -reset_timestamps 1 segments/death_01_%04d.mp4</code></p>

<p>Ensuite pour chaque segment on prépare des dossiers pour stocker les images intermédiaires en effaçant les anciens. Cela permet d'éviter de remplir son disque dur, vu qu'il y a plein de fichiers intermédiaires, et ça permet de facilement s'arrêter ou reprendre à un segment, ou de refaire le traitement d'un segment.</p>

<p>Du segment à traiter sont alors extraites 5 frames par seconde à intervale régulier. Ce sont ces images que nous allons traiter afin de déterminer s'il y est écrit "YOU DIED" dedans.</p>

<p><code>ffmpeg -i "$segment" -vf fps=5 "death_01_%04d.png"</code></p>

<p>Chaque image est alors découpée pour ne garder que la zone qui nous intéresse. Évidemment cela dépend du setup, qui a intérêt à ne pas changer d'une vidéo à l'autre (ou durant la vidéo) sinon il faut changer les paramètres.</p>

<p><code>convert "$image" -crop 420x90+342+274 "cropped.png"</code></p>

<h3>Chercher le texte</h3>

<p>Pour isoler la zone de texte on applique simplement un calque noir et blanc. Il dépend également du setup (et de la résolution) et doit être dessiné à la main en contourant les mots "YOU DIED" sur le screen d'une mort.</p>

<p><code>composite -compose Multiply "cropped.png" "mask-off.png" "masked.png"</code></p>

<p>On pousse ensuite la saturation à fond pour faire ressortir le rouge et mieux le détacher des autres couleurs. Ensuite on peint en noir tout ce qui n'est pas à peu près rouge.</p>
<p>Cette étape est loin d'être parfaite et ce n'est probablement pas la meilleur façon de faire tout ça, ni les meilleurs réglages de sensibilité. On est en particulier trop sensible aux couleurs jaune/orange alors qu'on préférerait ne s'intéresser qu'aux rouges foncés.</p>

<p><code>convert "masked.png" -modulate 100,500 "red.png"
convert "red.png" -fill Black -fuzz 25% +opaque Red "red.png"</code></p>

<p>Enfin on calcule le nombre de pixels rouges (enfin pas noirs) en comparant l'image résultante à une image toute noire.</p>

<p><code>convert "red.png" \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:</code></p>

<p>Si ce nombre est au dessus d'un certain seuil, on a peut-être un résultat positif. Pour être sûr que ce n'est pas tout l'écran qui est rouge, il faut tester le contour des mots. En effet ceux-ci sont affichés sur un fond noir, et donc cette zone ne doit pas être rouge.</p>

<p>Actuellement le seuil utilisé est de 2000 en 720p. La valeur moyenne sur les images trouvées est de l'ordre de 4000.</p>

<h3>Isoler le contour</h3>

<p>On refait globalement la même opération mais avec le masque inverse, qui ne laisse passer que le contour des mots.</p>

<p><code>composite -compose Multiply "crop.png" "mask-on.png" "maskx.png"
convert "maskx.png" -modulate 100,500 "redx.png"
convert "redx.png" -fill Black -fuzz 25% +opaque Red "redx.png"
convert "redx.png" \( +clone -evaluate set 0 \) -metric AE -compare -format "%[distortion]" info:</code></p>

<p>On compare le nombre de pixels rouge autour des mots à une valeur seuil et cette fois il en faut moins que le seuil pour s'assurer qu'on n'est pas juste face à une gerbe de sang ou un ciel orange.</p>

<p>Actuellement le seuil utilisé est de 2500 en 720p. Dans la plupart des images on est en dessous de 1500.</p>

<h3>Être content</h3>

<p>Quand une image de mort est trouvée, on la met de coté, histoire de pouvoir les compter ensuite et de vérifier si ce n'est pas un faux positif en regardant tout simplement si il s'agit bien d'une mort.</p>

<p>Ensuite on saute un certain nombre de frames (équivalent à 2 secondes) pour ne pas compter plusieurs fois une même mort.</p>

<p>Pendant mes tests j'ai conservé toutes les images qui étaient très rouges mais rejetées à cause du contour et il n'y avait aucune erreur, mais il y a beaucoup d'images rouges (sans même compter l'image de fond ou certaines ganaches). Sur les vidéos en 720p aucun faux positif ne s'est retrouvé validé par le procédé.</p>

<p>La 3eme VOD est en 360p parce que c'était le seul format disponible au moment où je l'ai récupérée. Mais la compression fait un peu trop baver l'image, du coup les tolérances étaient plus élevées et il y avait plein de faux positifs. Ce n'est pas grave, il suffit de les enlever, mais du coup j'ai préféré me cantonner au 720p plutôt que chercher à affiner les réglages du 360.</p>

<p>Il est assez difficile de déterminer s'il y a eu des faux négatifs, puisqu'il faudrait connaitre à l'avance une mort qui n'est pas dans la liste, mais si vous en voyez une, dites le moi. En tout cas le comptage automatisé des morts s'est révélé plus efficace que le comptage humain !</p>

<p>Enfin le procédé prend entre 30s et 45s pour traiter un segment d'une minute, n'utilise qu'un core de processeur, bien qu'on puisse lancer le script plusieurs fois en parallèle en faisant plusieurs lots de segments de vidéo (attention à ne pas mélanger les fichiers intermédiaires)</p>

<h3>Divers et d'été</h3>

<p>Il faut noter qu'on ne prend pas forcément l'image où le message "YOU DIED" est le mieux affiché, mais la première image trouvée pour chaque mort. On pourrait améliorer les screens en ne sautant pas d'images mais en prenant la meilleure (celle dont le score de pixels rouges est le plus élevé).</p>

<p>Le procédé pourrait être optimisé de bien des façons. Pour commencer on pourrait utiliser moins de fichiers intermédiaires en combinant des opérations en mémoire (il me semble que Imagemagick peut faire ça).</p>

<h3>Le faire en live</h3>

<p>Actuellement le script prend une video et en extraie des frames.</p>

<p>À mon avis, si on a accès à un stream direct, le plus simple doit être de le dumper sur le disque sous forme de segments d'une minutes ou de quelques secondes (pour être plus réactif), et de lancer le script sur chaque segment dès qu'il est disponible, quitte à le lancer plusieurs fois en parallèle si les traitements sont plus longs que les segments.</p>

<p>Sinon, il est potentiellement envisageable d'utiliser un outil de capture d'écran pour extraire des frames au fur et à mesure du stream, à condition de bien caler la capture avec le setup et d'extraire la bonne partie de l'image. Et de pouvoir capturer 5 frames par seconde.</p>

<h3>Ah oui au fait</h3>

<p>Tout ça je le fais avec des outils open source en ligne de commande tranquilou, c'est un script bash et ça utilise ffmpeg et Imagemagick. Et non je ne fais pas ça sous windows, mais c'est surement possible avec cygwin ou Windows 10 et son WSL (ou double-vaisselle).</p>

</div>
</body>
</html>
