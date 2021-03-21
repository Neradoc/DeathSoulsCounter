#!/usr/bin/env python

import argparse, math, atexit
import requests, hmac, hashlib
import subprocess,re,time,glob,os,shutil,configparser
from multiprocessing import Process, Queue, SimpleQueue, Pool

DEBUG = False
DIAGNOS = False

# le dossier où ça se passe
DIR = "_streams/"
# dossier des morts trouvées
DIRFOUND = DIR+"found/"
# dossier des morts réelles (après tri)
DIRTRUE = DIR+"deaths/"
# dossier des images temporaires
DIRIMG = DIR+"img/"
# dossier des segments temporaires
DIRVID = DIR+"ivid/"
# chemin de la vidéo source
SOURCE = DIR+"stream.mpg"

# exécutables ffmpeg/libav
FFMPEG_EXE = "ffmpeg"
FFMPEG_PROBE = "ffprobe"

# exécutables imagemagick
IMGMGK_COMP = "composite"
IMGMGK_CONV = "convert"

# numéro de la vidéo/session (incrémenter pour les avoir dans l'ordre)
NUMVID = str(int(1000*time.time()))
# formats des noms des fichiers (la partie après le num de la vidéo)
FORMATNOM = ""
# format des images utilisées pour la capture (jpg)
IMGEXT = "jpg"

# intervalle entre deux analyses (5) (secondes minimum dispo avant analyse)
timeStep = 5
# nombre de frames extraites par seconde (5)
FPS = 5
# nombre maximum de process simultanés d'analyse vidéo (1)
MAXPROCESS = 1
# effacer les fichiers intermédiaires (True)
DELETE = True
# upload les images sur le site (paramétrer) (False)
UPLOADFILES = False
# nombre de secondes min entre deux morts (4)
TIMEMARGIN = 4
# point de départ (pour communiquer aux sous process)
STARTAT = 0
# durée maximum
MAXLENGTH = 0
# temps à ajouter aux temps formatés (en secondes)
TIMERADD = 0
# temps de départ
STARTTIME = time.time()

# clef magique
MAGICKEY = b"REMPLACEZ MOI PAR LA CLEF SECRETE"
# page d'upload
UPLOADURL = 'https://quelquepart/chemin/compteur.php'

# cropage
CROPDIMS="212x48+171+134"
# nb dans le masque: 3741
MINPIXELON=800
# nb dans le masque: 6435
MAXPIXELOFF=1000
# masques
MASKON = "360/mask-on.png"
MASKOFF= "360/mask-off.png"

#####################################################################
#####################################################################

# pour le bug dans python pour MacOSX qui nique la ligne de commande
def restoreCommandLine():
	subprocess.call(["stty","echo"])

#####################################################################
#####################################################################

def safeInt(input,defo=0):
	try:
		return int(input)
	except:
		return defo

#####################################################################
#####################################################################

def init_dirs():
	global DIR,DIRFOUND,DIRTRUE,DIRIMG,DIRVID,SOURCE
	DIRFOUND = DIR+"found/"
	DIRTRUE = DIR+"deaths/"
	DIRIMG = DIR+"img/"
	DIRVID = DIR+"ivid/"
	SOURCE = DIR+"stream.mpg"
	for thedir in [DIRFOUND,DIRTRUE,DIRIMG,DIRVID]:
		if not os.path.exists(thedir):
			os.mkdir(thedir)

#####################################################################
#####################################################################

def init_res(res = "720fr"):
	global CROPDIMS, MINPIXELON, MAXPIXELOFF, MASKON, MASKOFF
	setupFile = res+"/setup.ini"
	if os.path.exists(setupFile):
		setup = configparser.ConfigParser()
		setup.read(setupFile)
		CROPDIMS = setup.get("masks","CROPDIMS",fallback="10x10+100+20")
		MINPIXELON = setup.get("masks","MINPIXELON",fallback="2000")
		MINPIXELON = safeInt(MINPIXELON, 2000)
		MAXPIXELOFF = setup.get("masks","MAXPIXELOFF",fallback="4000")
		MAXPIXELOFF = safeInt(MAXPIXELOFF, 4000)
		MASKON = res+"/mask-on.png"
		MASKOFF= res+"/mask-off.png"
	print("CROPDIMS : "+str(CROPDIMS))
	print("MINPIXELON : "+str(MINPIXELON))
	print("MAXPIXELOFF : "+str(MAXPIXELOFF))
	print("MASKON : "+str(MASKON))
	print("MASKOFF : "+str(MASKOFF))

#####################################################################
#####################################################################

def formate_le_temps(timeStamp, isFrames=False):
	if isFrames:
		timeStamp = timeStamp / FPS
	heures = math.floor(timeStamp / 60 / 60)
	minutes = math.floor(timeStamp / 60) % 60
	secondes = math.floor(timeStamp) % 60
	return "%dh%02dm%02ds" % (heures,minutes,secondes)
	

#####################################################################
#####################################################################

def traite_la_mort(imageFile,imageName,remplace=""):
	if UPLOADFILES:
		UPLOADTRIES = 5
		tries = UPLOADTRIES
		while tries > 0:
			try:
				filehandle = open(imageFile, "rb")
				filecode = hmac.new(MAGICKEY.encode(), imageName.encode('utf-8'), hashlib.sha1).hexdigest()
				files = { 'file': (imageName, filehandle)}
				data = {'filecode': filecode, 'remplace': remplace}
				res = requests.post(UPLOADURL, files=files, data=data)
				if res.text[0:2] != "OK":
					print("UPLOAD ERROR "+imageName)
				filehandle.close()
				return "OK"
			except Exception as e:
				print("ERREUR RESEAU - ON RETENTE 2 OU 3 FOIS GENRE")
				print(e)
				time.sleep(0.01)
				tries = tries - 1

#####################################################################
#####################################################################

def analyse_les_found(foundQueue):
	allTheFound = list()
	zoneDeRecherche = MAXPROCESS * FPS * TIMEMARGIN
	while 1:
		(nomImage, segmentTime, pixelOn) = foundQueue.get()
		if nomImage == 0: break;
		# trouver la frame dans le nom du fichier (1-based donc -1)
		match = re.search(r"death_(\d+)_(\d+)\."+IMGEXT,nomImage)
		frame = int(match.group(2)) - 1
		timeStamp = segmentTime + frame / FPS + TIMERADD
		# vrai "beau" nom
		if FORMATNOM == "HMS":
			fullNom = "death_"+NUMVID+"_%s_%d.%s" % (formate_le_temps(timeStamp), frame, IMGEXT)
		else:
			fullNom = "death_"+NUMVID+"_%07.1f.%s" % (timeStamp,IMGEXT)
		# trouver les images dont le timestamp est proche
		exists = False
		iStart = max(0,len(allTheFound)-zoneDeRecherche)
		iEnd = len(allTheFound)
		for iFound in range(iStart,iEnd):
			(iNomImage, iTimeStamp, iPixelOn) = allTheFound[iFound]
			if abs(iTimeStamp-timeStamp) < TIMEMARGIN:
				exists = True
				if pixelOn > iPixelOn:
					# remplacer iFound
					print("BETTER ! %s (%d vs %d)" % (fullNom,pixelOn,iPixelOn))
					allTheFound[iFound] = (fullNom, timeStamp, pixelOn)
					shutil.move(DIRFOUND+nomImage,DIRTRUE+fullNom)
					os.remove(DIRTRUE+iNomImage)
					# réupload à chaque fois
					traite_la_mort(DIRTRUE+fullNom,fullNom,remplace=iNomImage)
				else:
					# effacer le notre
					os.remove(DIRFOUND+nomImage)
				break
		# enregistrer l'image et sa quantité de rouge
		if not exists:
			print("\nFOUND !! %s > %s (%d)" % (nomImage,fullNom,pixelOn))
			allTheFound += [(fullNom, timeStamp, pixelOn)]
			shutil.move(DIRFOUND+nomImage,DIRTRUE+fullNom)
			traite_la_mort(DIRTRUE+fullNom,fullNom)
	#
	return foundQueue.put(allTheFound)

#####################################################################
#####################################################################

def analyse_image(foundQueue,segmentTime,fichierImage):
	nomImage = os.path.basename(fichierImage)
	# croper
	com = [IMGMGK_CONV, fichierImage, "-crop", CROPDIMS, fichierImage+".c.png"]
	subprocess.call(com)
	
	# appliquer le masque, appliquer les seuils, calculer les pixels
	tPIXELON = subprocess.check_output([IMGMGK_CONV,
		"-compose", "Multiply", MASKOFF, fichierImage+".c.png", "-composite",
		"-modulate", "100,500", "-fill", "Black", "-fuzz", "25%", "+opaque", "Red",
		"(", "+clone", "-evaluate", "set", "0", ")", "-metric", "AE", "-compare", "-format", "%[distortion]", "info:"])
	PIXELON = int(tPIXELON)
	
	if DEBUG:
		# appliquer le masque
		com = [IMGMGK_COMP, "-compose", "Multiply", fichierImage+".c.png", MASKOFF, fichierImage+".m.png"]
		subprocess.call(com)
		# appliquer les seuils
		com = [IMGMGK_CONV, fichierImage+".m.png", "-modulate", "100,500", "-fill", "Black", "-fuzz", "25%", "+opaque", "Red", fichierImage+".r.png"]
		subprocess.call(com)
	
	if DEBUG:
		# appliquer le masque, appliquer les seuils, calculer les pixels
		tPIXELOFF = subprocess.check_output([IMGMGK_CONV,
			"-compose", "Multiply", MASKON, fichierImage+".c.png", "-composite",
			"-modulate", "100,500",
			"-fill", "Black", "-fuzz", "25%", "+opaque", "Red",
			"(", "+clone", "-evaluate", "set", "0", ")", "-metric", "AE", "-compare", "-format", "%[distortion]", "info:"])
		PIXELOFF = int(tPIXELOFF)
		print("---- %s : %d / %d" % (nomImage,PIXELON,PIXELOFF))
		
	
	if PIXELON > MINPIXELON:
		# appliquer le masque, appliquer les seuils, calculer les pixels
		if not DEBUG:
			tPIXELOFF = subprocess.check_output([IMGMGK_CONV,
				"-compose", "Multiply", MASKON, fichierImage+".c.png", "-composite",
				"-modulate", "100,500",
				"-fill", "Black", "-fuzz", "25%", "+opaque", "Red",
				"(", "+clone", "-evaluate", "set", "0", ")", "-metric", "AE", "-compare", "-format", "%[distortion]", "info:"])
			PIXELOFF = int(tPIXELOFF)
	
		if DEBUG:
			# appliquer le masque
			com = [IMGMGK_COMP, "-compose", "Multiply", fichierImage+".c.png", MASKON, fichierImage+".n.png"]
			subprocess.call(com)
			# appliquer les seuils
			com = [IMGMGK_CONV, fichierImage+".n.png", "-modulate", "100,500", fichierImage+".q.png"]
			subprocess.call(com)
			com = [IMGMGK_CONV, fichierImage+".q.png", "-fill", "Black", "-fuzz", "25%", "+opaque", "Red", fichierImage+".q.png"]
			subprocess.call(com)

		#print("%s: %6d /%6d" % (nomImage, PIXELON, PIXELOFF))
		if PIXELOFF < max( MAXPIXELOFF, 0.5 * PIXELON ):
			#print("FOUND !! "+nomImage)
			shutil.copyfile(fichierImage,DIRFOUND+nomImage)
			foundQueue.put( (nomImage,segmentTime,PIXELON) )
	
	if DELETE:
		for image in glob.glob(fichierImage+".*"):
			os.remove(image)
	
	return (PIXELON > MINPIXELON)

#####################################################################
#####################################################################

def analyse_video(segmentTime, syncQueue, foundQueue):
	# diagnostics
	nPixon = 0
	temps_debut = time.time()
	vid_ext = os.path.splitext(SOURCE)[1]
	#
	t_segmentTime = str(segmentTime)
	p_segmentTime = "%05d" % (segmentTime)
	#print("P"+p_segmentTime+" START")
	#
	FNULL = open(os.devnull, 'w')
	#ffmpeg -i "$DIR/stream.mp4" -ss "$segmentTime" -t "$timeStep" -vf fps=5 "$DIR/img/death_$segmentTime_%04d.png"
	###command = [FFMPEG_EXE, "-i", SOURCE, "-ss", segmentTime, "-t", str(timeStep), "-vf", "fps="+str(fps), DIR+"/img/death_"+p_segmentTime+"_%04d.jpg"]
	###subprocess.call(command, stdout=FNULL, stderr=FNULL)

	# on découpe la section de la vidéo correspondant (sans réencodage, sans le son)
	# -ss AVANT le -i change la façon dont ça marche (fast seek avant, lent après)
	command = [FFMPEG_EXE, "-y", "-ss", t_segmentTime, "-i", SOURCE, "-c", "copy", "-an", "-t", str(timeStep), DIRVID+"stream-"+p_segmentTime+vid_ext]
	subprocess.call(command, stdout=FNULL, stderr=FNULL)
	
	# on crée les images dans le dossier img en les taggant avec segmentTime
	command = [FFMPEG_EXE, "-y", "-i", DIRVID+"stream-"+p_segmentTime+vid_ext, "-vf", "fps="+str(FPS), "-q:v", "1", DIRIMG+"death_"+p_segmentTime+"_%04d."+IMGEXT]
	subprocess.call(command, stdout=FNULL, stderr=FNULL)
	
	##temps_ffmpeg = "%0.2f" % (time.time() - temps_debut)
	
	# pour chaque image
	images = list(glob.glob(DIRIMG+"death_"+p_segmentTime+"_*."+IMGEXT))
	
	for image in images:
		# faire tout le boulot sur les images
		(isPixon) = analyse_image(foundQueue,segmentTime,image)
		if isPixon: nPixon += 1
	
	# rm
	if DELETE:
		os.remove(DIRVID+"stream-"+p_segmentTime+vid_ext)
		for image in images:
 			os.remove(image)
	
	# calculs de temps et diagnostics
	if DIAGNOS:
		temps_total = "%0.2f" % (time.time() - temps_debut)
		speedup = timeStep / (time.time() - temps_debut)
		pctOn = "%0.1f" % ( 100 * nPixon/len(images) )
		avance = (segmentTime + timeStep - STARTAT) - (time.time() - STARTTIME)
		global_speedup = (segmentTime + timeStep - STARTAT) / (time.time() - STARTTIME)
		#
		print(
			"P"+ ("%05d" % (segmentTime+TIMERADD))
			+" Avance:%.1fs" % (avance)
			+" (%0.2fx)" % (global_speedup)
			+" Segment:"+temps_total+"s"
			+" (%0.2fx)" % (speedup)
			+" ON:"+pctOn+"%"
			+" T:"+formate_le_temps(segmentTime)
			+"\n"
		)
	else:
		print(".",end="",flush=True)
	syncQueue.put(segmentTime)

#####################################################################
#####################################################################

def videoLength():
	bytes = subprocess.check_output([FFMPEG_PROBE, "-i", SOURCE, "-show_format", "-v", "quiet"])
	data = str(bytes,'utf-8')
	match = re.search(r"duration=(\d+\.\d*)",data)
	duration = float(match.group(1))
	return duration

#####################################################################
#####################################################################

def processStream(isLive = True):
	print("Procs:%d\nStep:%d\nVideo:%s\nLive:%s\nUpload:%s"
		% (MAXPROCESS, timeStep, SOURCE, ("non","oui")[isLive], ("non","oui")[UPLOADFILES]) )
	if not os.path.exists(SOURCE):
		print("La vidéo SOURCE n'existe pas !! "+SOURCE)
		exit()
	if DELETE:
		for file in glob.glob(DIRIMG+"*"):
			os.remove(file)
		for file in glob.glob(DIRVID+"*"):
			os.remove(file)
	syncQueue = Queue()
	foundQueue = Queue()
	# temps analysé (secondes depuis le début de la vidéo)
	segmentTime = STARTAT
	# nombre de process en cours
	nProcess = 0
	# lancer un process qui va attendre de façon bloquante sur la foundQueue
	# et sélectionner les images qu'il reçoit
	pAnalyseLesFound = Process(target=analyse_les_found, args=(foundQueue,))
	pAnalyseLesFound.start()
	while True:
		# tester la durée de la vidéo
		duration = videoLength()
		
		# tant qu'il reste de la vidéo à traiter (duration > segmentTime)
		# - attendre qu'il y ait des workers de libre
		# - traiter des segments
		
		while duration > segmentTime + timeStep:
			if nProcess >= MAXPROCESS:
				out = syncQueue.get()
				nProcess -= 1
			# ICI on lance un process
			#analyse_video(syncQueue,segmentTime,deltaT,foundQueue)
			p = Process(target=analyse_video, args=(segmentTime, syncQueue, foundQueue,))
			p.start()
			nProcess += 1
			# passage au step suivant
			segmentTime += timeStep
			# test de la durée maximum
			if MAXLENGTH > 0:
				if segmentTime >= STARTAT + MAXLENGTH:
					break
			# marqueur de temps à intervalle régulier
			if segmentTime % (5*60) < timeStep:
				print(formate_le_temps(segmentTime))

		
		# quand on a traité tous les segments
		# - si on n'est pas sur un live, traiter le dernier segment
		# - si on est sur un live, boucler
		if not isLive: break
	
	if MAXLENGTH == 0:
		p = Process(target=analyse_video, args=(segmentTime, syncQueue, foundQueue,))
		p.start()
		nProcess += 1

	# attendre les process d'analyse vidéo
	while nProcess > 0:
		out = syncQueue.get()
		nProcess -= 1
	# fermer le process d'analyse des found
	foundQueue.put((0,0,0))
	pAnalyseLesFound.join()
	# on a fini !
	totalTime = time.time() - STARTTIME
	print("\n")
	print("Temps écoulé: %.1f" % (totalTime))
	print("Temps analysé: %.1f" % (duration))
	print("Efficacité: %.1fx" % (duration / totalTime))
	
#####################################################################
#####################################################################

def processImages():
	foundQueue = Queue()
	images = glob.glob(DIRIMG+"death_*."+IMGEXT)
	# lancer un process qui va attendre de façon bloquante sur la foundQueue
	# et sélectionner les images qu'il reçoit
	pAnalyseLesFound = Process(target=analyse_les_found, args=(foundQueue,))
	pAnalyseLesFound.start()
	for fichierImage in images:
		match = re.search(r"death_(\d+)_(\d+)\."+IMGEXT,fichierImage)
		segmentTime = int(match.group(1))
		print(".",end="")
		analyse_image(foundQueue,segmentTime,fichierImage)
	foundQueue.put((0,0,0))
	pAnalyseLesFound.join()
	allTheFound = foundQueue.get()
	print("\nOn a trouvé %d morts !!" % (len(allTheFound)))

#####################################################################
#####################################################################

if __name__ == '__main__':
	# pour le bug python MacOSX
	atexit.register(restoreCommandLine)
	# sélectionner images / stream / video selon les paramètres
	# image trie les images found
	# - les mettre dans deaths
	# - supprimer de found ? ou quoi ?
	# stream parse le stream
	# video s'arrête à la fin de la video
	parser = argparse.ArgumentParser()
	parser.add_argument('--numsession', '-n', help='Numéro de la session (numéro de la VOD)') # required=True
	parser.add_argument('--images', '-i', action='store_true', help='Analyser les images au lieu de la video')
	parser.add_argument('--video', '-v', action='store_true', help='Analyser une vidéo fixe plutôt que le stream')
	parser.add_argument('--upload', '-u', action='store_true', help='Uploader les vidéos sur le site')
	parser.add_argument('--uploadurl', help='Url du script d\'upload des fichiers')
	parser.add_argument('--uploadkey', help='Clef de sécurité pour le script')
	parser.add_argument('--procs', '-p', help='Nombre maximum de process (1-8 typiquement)')
	parser.add_argument('--step', '-s', help='Longueur du pas (en secondes)')
	parser.add_argument('--maskdir', '-m', help='Dossier des données de masques')
	parser.add_argument('--dir', help='Dossier racine des fichiers temporaires et de sortie')
	parser.add_argument('--source', help='Chemin d\'accès du fichier vidéo source')
	parser.add_argument('--format', help='Format du timestamp du nom des fichiers (HMS)')
	parser.add_argument('--startat', help='Point de départ de l\'analyse (en secondes)')
	parser.add_argument('--length', help='S\'arrêter après avoir analysé cette durée')
	parser.add_argument('--addtime', help='Temps à ajouter au compteur lors de la création de fichier')
	parser.add_argument('--nodelete', action='store_true', help='Ne pas effacer les fichiers temporaires')
	parser.add_argument('--diagnos', action='store_true', help='Afficher les messages de diagnostique')
	parser.add_argument('--debug', action='store_true', help='Créer des fichiers temporaires supplémentaires')
	parser.add_argument('--png', action='store_true', help='Générer les captures en PNG (jpg par défaut)')
	args = parser.parse_args()
	#
	try:
		if int(args.procs) > 0:
			MAXPROCESS = int(args.procs)
	except:
		pass
	#
	try:
		if int(args.step) > 0:
			timeStep = int(args.step)
	except:
		pass
	#
	try:
		if int(args.length) > 0:
			MAXLENGTH = int(args.length)
	except:
		pass
	#
	try:
		if int(args.addtime) > 0:
			TIMERADD = int(args.addtime)
	except:
		pass
	#
	if args.upload:
		UPLOADFILES = True
	#
	if args.uploadurl:
		UPLOADURL = args.uploadurl
	#
	if args.uploadkey:
		MAGICKEY = args.uploadkey
	#
	if args.maskdir:
		init_res(args.maskdir)
	else:
		init_res()
	#
	if args.numsession:
		NUMVID = args.numsession
	#
	if args.dir:
		if os.path.exists(args.dir):
			DIR = args.dir
			if DIR[-1:] != "/":
				DIR = DIR + "/"
			init_dirs()
	#
	if args.source:
		SOURCE = args.source
	#
	if args.nodelete:
		DELETE = False
	#
	if args.diagnos:
		DIAGNOS = True
	#
	if args.debug:
		DEBUG = True
	#
	if args.png:
		IMGEXT = "png"
	#
	if args.format:
		FORMATNOM = args.format
	#
	startat = 0
	if args.startat:
		mat = re.match(r'(\d+)h(\d+)m(\d+)s',args.startat)
		if mat:
			STARTAT = int(mat.group(1))*60*60+int(mat.group(2))*60+int(mat.group(3))
		else:
			try:
				if int(args.startat) >= 0:
					STARTAT = int(args.startat)
			except:
				pass
	# TODO: tester l'existence de DIR / créer les sous dossiers	
	#
	if args.images:
		processImages()
	elif args.video:
		processStream(isLive = False)
	else:
		processStream(isLive = True)
