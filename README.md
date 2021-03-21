# DeathSoulsCounter
Compteur de morts dans Dark Souls pour Realmyop


## Avant Propos

## Utilisation de base
1. installer le site
	- installer les scripts php quelque part
	- personnaliser la magickey sur le site et localement
2. installer les utilitaires du script
	- imagemagick
	- ffmpeg (pas libav/avtools)
	- livestreamer (pip)
3. configurer le streaming
	- créer un TWITCH_AUTH à soi pour l'utiliser
4. configurer la reconnaissance d'images
	- trouver les valeurs de crop pour le setup
	- créer les masques correspondant au setup
	- créer le fichier n'ini
	- faire des tests en local pour déterminer MIN ON et MAX OFF
5. lancer les scripts pendant le stream
	- voir le script de démo startstreamer
	- lancer livestreamer pour créer le fichier vidéo
	- lancer l'analyse de la vidéo pour extraire les morts

## Installer le site

## Installation des outils sur OVH VPS
- apt-get install python-setuptools python-dev build-essential
- easy_install pip
- pip2.7 install livestreamer
- apt-get install ffmpeg
- apt-get install imagemagick


## Explication du fonctionnement

## Description des composantes

## Informations utiles supplémentaires

## Kappa Kappa Kappa
