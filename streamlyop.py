#!/usr/bin/env python

import subprocess,re,time,glob,os,shutil
from multiprocessing import Process, Queue, Pool

DIR = "_streams_/"
VID = "stream.mpg"
EXT = "png"
timeStep = 5
fps = 5
MAXPROCESS = 4
nProcess = 0
DELETE = True
DEBUG = False
START_TIME = time.time()
deltaT = 0

print("livestreamer twitch.tv/realmyop2 source -o _streams_/stream.mpg")

res = "720fr"

if res == "360":
	# cropage
	cropDims="212x48+171+134"
	# nb dans le masque: 3741
	MINPIXELON=800
	# nb dans le masque: 6435
	MAXPIXELOFF=1000
	# masques
	MASKON = "360/mask-on.png"
	MASKOFF= "360/mask-off.png"
elif res == "720":
	# cropage
	cropDims="420x90+342+274"
	# nb dans le masque: 12801
	MINPIXELON=2300
	# nb dans le masque: 24999
	MAXPIXELOFF=2500
	# masques
	MASKON = "720/mask-on.png"
	MASKOFF= "720/mask-off.png"
elif res == "720fr":
	#cropage
	cropDims="694x84+204+284"
	# nb dans le masque: 12801
	MINPIXELON=2300
	# nb dans le masque: 24999
	MAXPIXELOFF=2500
	# masques
	MASKON = "720fr/mask-on.png"
	MASKOFF= "720fr/mask-off.png"

#####################################################################
#####################################################################

def analyse_image(fichierImage, dossierFound):
	nomImage = os.path.basename(fichierImage)
	# croper
	com = ["convert", fichierImage, "-crop", cropDims, fichierImage+".c."+EXT]
	subprocess.call(com)
	
	# appliquer le masque, appliquer les seuils, calculer les pixels
	tPIXELON = subprocess.check_output(["convert",
		"-compose", "Multiply", MASKOFF, fichierImage+".c."+EXT, "-composite",
		"-modulate", "100,500", "-fill", "Black", "-fuzz", "25%", "+opaque", "Red",
		"(", "+clone", "-evaluate", "set", "0", ")", "-metric", "AE", "-compare", "-format", "%[distortion]", "info:"])

	if DEBUG:
		# appliquer le masque
		com = ["composite", "-compose", "Multiply", fichierImage+".c."+EXT, MASKOFF, fichierImage+".m."+EXT]
		subprocess.call(com)
		# appliquer les seuils
		com = ["convert", fichierImage+".m."+EXT, "-modulate", "100,500", "-fill", "Black", "-fuzz", "25%", "+opaque", "Red", fichierImage+".r."+EXT]
		subprocess.call(com)
		# calculer les pixels
		tPIXELON = subprocess.check_output(["convert", fichierImage+".r."+EXT, "(", "+clone", "-evaluate", "set", "0", ")", "-metric", "AE", "-compare", "-format", "%[distortion]", "info:"])

	PIXELON = int(tPIXELON)
	
	if PIXELON > MINPIXELON:
		# appliquer le masque, appliquer les seuils, calculer les pixels
		tPIXELOFF = subprocess.check_output(["convert",
			"-compose", "Multiply", MASKON, fichierImage+".c."+EXT, "-composite",
			"-modulate", "100,500", "-fill", "Black", "-fuzz", "25%", "+opaque", "Red",
			"(", "+clone", "-evaluate", "set", "0", ")", "-metric", "AE", "-compare", "-format", "%[distortion]", "info:"])
		
		if DEBUG:
			# appliquer le masque
			com = ["composite", "-compose", "Multiply", fichierImage+".c."+EXT, MASKON, fichierImage+".n."+EXT]
			subprocess.call(com)
			# appliquer les seuils
			com = ["convert", fichierImage+".n."+EXT, "-modulate", "100,500", fichierImage+".q."+EXT]
			subprocess.call(com)
			com = ["convert", fichierImage+".q."+EXT, "-fill", "Black", "-fuzz", "25%", "+opaque", "Red", fichierImage+".q."+EXT]
			subprocess.call(com)
			# calculer les pixels
			tPIXELOFF = subprocess.check_output(["convert", fichierImage+".q."+EXT, "(", "+clone", "-evaluate", "set", "0", ")", "-metric", "AE", "-compare", "-format", "%[distortion]", "info:"])

		PIXELOFF = int(tPIXELOFF)
	
		#print("%s: %6d /%6d" % (nomImage, PIXELON, PIXELOFF))
		if PIXELON > MINPIXELON and PIXELOFF < MAXPIXELOFF:
			print("FOUND !! "+nomImage)
			shutil.copyfile(fichierImage,dossierFound+nomImage)
	
	if DELETE:
		for image in glob.glob(fichierImage+".*"):
			os.remove(image)
	
	return (PIXELON > MINPIXELON)

#####################################################################
#####################################################################

def analyse_video(queue,advance,deltaT):
	# diagnostics
	nPixon = 0
	temps_debut = time.time()
	#
	t_advance = str(advance)
	p_advance = "%05d" % (advance)
	out_print = ""
	print("P"+p_advance+" START")
	#
	FNULL = open(os.devnull, 'w')
	#ffmpeg -i "$DIR/stream.mp4" -ss "$advance" -t "$timeStep" -vf fps=5 "$DIR/img/death_$advance_%04d.png"
	###command = ["ffmpeg", "-i", DIR+VID, "-ss", advance, "-t", str(timeStep), "-vf", "fps="+str(fps), DIR+"/img/death_"+p_advance+"_%04d.jpg"]
	###subprocess.call(command, stdout=FNULL, stderr=FNULL)

	# on découpe la section de la vidéo correspondant (sans réencodage, sans le son)
	# -ss AVANT le -i change la façon dont ça marche (fast seek avant, lent après)
	command = ["ffmpeg", "-y", "-ss", t_advance, "-i", DIR+VID, "-an", "-t", str(timeStep), DIR+"ivid/stream-"+p_advance+".mpg"]
	subprocess.call(command, stdout=FNULL, stderr=FNULL)
	
	# on crée les images dans le dossier img en les taggant avec advance
	command = ["ffmpeg", "-y", "-i", DIR+"ivid/stream-"+p_advance+".mpg", "-vf", "fps="+str(fps), "-q:v", "1", DIR+"img/death_"+p_advance+"_%04d.jpg"]
	subprocess.call(command, stdout=FNULL, stderr=FNULL)
	
	temps_ffmpeg = "%0.2f" % (time.time() - temps_debut)
	if DEBUG:
		out_print += "    -- TIME FF: "+temps_ffmpeg+"\n"
	
	# pour chaque image
	images = list(filter(
		lambda x: not re.search("jpg\..*\.png",x), 
		glob.glob(DIR+"/img/death_"+p_advance+"_*.jpg")
	))
	
	for image in images:
		# faire tout le boulot sur les images
		(isPixon) = analyse_image(image,DIR+"/found/")
		if isPixon: nPixon += 1
	
	if DEBUG:
		out_print += "    -- N images: %d ON: %d\n" % (len(images),nPixon)
	
	# rm
	if DELETE:
		os.remove(DIR+"ivid/stream-"+p_advance+".mpg")
		for image in images:
 			os.remove(image)
	
	# calculs de temps et diagnostics
	temps_total = "%0.2f" % (time.time() - temps_debut)
	speedup = "%0.2f" % ( (advance + timeStep) / (time.time() - START_TIME))
	pctOn = "%0.1f" % ( 100 * nPixon/len(images) )
	#
	out_print += "    -- dT: "+( "%0.1f" %(deltaT) )+" Acc:"+speedup+" Total: "+temps_total+" ON: "+pctOn+"% \n"
	print("P"+p_advance+" FINISHED\n"+out_print)
	queue.put(advance)

#####################################################################
#####################################################################

if __name__ == '__main__':
	if DELETE:
		for file in glob.glob(VID+"img/*"):
			os.remove(file)
		for file in glob.glob(VID+"ivid/*"):
			os.remove(file)
	queue = Queue()
	advance = 0
	while 1:
		#DURATION=`ffprobe -i tests/stream.mp4 -show_format -v quiet | sed -n 's/duration=//p'`
		bytes = subprocess.check_output(["ffprobe", "-i", DIR+VID, "-show_format", "-v", "quiet"])
		data = str(bytes,'utf-8')
		match = re.search(r"duration=(\d+)",data)
		duration = int(match.group(1))
	
		if duration < advance + timeStep:
			time.sleep(0.01)
			deltaT += 0.01
			continue
	
		if nProcess < MAXPROCESS:
			nProcess += 1
			# ICI on lance un thread (ou un process)
			#analyse_video(queue,str(advance))
			p = Process(target=analyse_video, args=(queue,advance,deltaT,))
			p.start()
			advance += timeStep
			deltaT = 0
		else:
			#print("TOO MANY PROCESS : %d" %(nProcess))
			pass
		
		try:
			out = queue.get(False)
			nProcess -= 1
		except:
			pass
