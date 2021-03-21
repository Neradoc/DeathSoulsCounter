#!/bin/sh
#exit

green2="\x1b[1;92m"
yellow2="\x1b[1;93m"
cyan2="\x1b[1;96m"
noc="\x1b[0m"

alias livestreamer="/Library/Frameworks/Python.framework/Versions/2.7/bin/livestreamer"
STREAM_DIR="_streams"
CHANNEL="realmyop2"
TWITCH_AUTH="votretwitchauthàcréerutilisezpaslamienne"
UPLOAD_URL='https://realmyop.fr/darksouls'
UPLOAD_KEY='VOTREUPLOADKEYSECRETEAMETTRESURLESITE'

#
echo "$cyan2 Télécharger le stream $noc"
echo "mv \"$STREAM_DIR/stream.mpg\" \"$STREAM_DIR/stream-\`date\`.mpg\"; livestreamer --twitch-oauth-token $TWITCH_AUTH \"twitch.tv/$CHANNEL\" source --quiet -o \"$STREAM_DIR/stream.mpg\""

echo "$green2 Analyser le stream $noc"
echo "python3.4 analyse_video.py -m 720fr2 -p 2 -n \`date +%s\` -u --dir \"$STREAM_DIR\" --source \"$STREAM_DIR/stream.mpg\" --diagnos --format HMS --uploadurl \"$UPLOAD_URL/compteur.php\" --uploadkey '$UPLOAD_KEY'"

# CONVERTIR les VOD en fichier stream pour le traiter
# ffmpeg -i stream.mp4 -qscale:v 8 stream.mpg
# conseil: mpg de bonne qualité, pas de --png

echo "$yellow2 Analyser une VOD $noc"
echo "python3.4 analyse_video.py -m 720fr2 -p 3 -n xx --dir \"$STREAM_DIR\" --source \"$STREAM_DIR/stream_missing.mpg\" --video --diagnos --format HMS"
