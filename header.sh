#!/bin/sh

DIR="/Users/spyro/_exclus_de_timemachine/realmyop"
FPS=5
# résolution
res=720

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
