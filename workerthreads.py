import threading
from parameters import Parameters
import time
import datetime
stopWatchStartTime = 0
def stopWatchStart():
	global stopWatchStartTime
	curr_dt = datetime.datetime.now()
	stopWatchStartTime = curr_dt.timestamp()
def stopWatchStop():
	global stopWatchStartTime
	curr_dt = datetime.datetime.now()
	stopWatchEndTime = curr_dt.timestamp()
	return stopWatchEndTime - stopWatchStartTime

threads = Parameters({}) #A parameters object to hold and catalog all threads being created

class workerThread(threading.Thread):
	def __init__(self, *args, **kwargs): #name, menuLevel
		super(workerThread, self).__init__(None, **kwargs)
		self._stop = threading.Event()
		P = {}
		self.P = Parameters(P)
		self.P.set("outputImage", None)
		self.P.setDescription("outputImage", "What image is the thread outputting")
		self.outputVisual = False #For other threads to know and act upon
		self.name = args[0]
		self.P.set("Menu Level", args[1])
		threads.set(self.name, self) #Add it to the threads globals
		#Variables to track changes to the database and buffer inputs while the thread is processing
		self.waiting_cycles = 0
		self.update_buffer = {}
		self.is_processing = False
		self.is_updating = False
	
	# function using _stop function
	def stop(self):
		self._stop.set()
		self.P.set("outputImage",None)
		self.outputVisual = False

	def stopped(self):
		return self._stop.isSet()

	def __str__(self): #Return the threads status
		ret = ""
		if self.stopped():
			ret += "{} stopped\n".format(self.name)
		else:
			ret += "{} running\n".format(self.name)
		return str(self.P)

	#True if the thread has new information
	def updated(self):
		return self.P.updated
	
	#Run once the update is processed
	def updateProcessed(self):
		self.P.updated = False
	
	def getOutputImage(self):
		img = self.P.get("outputImage")
		self.P.parameter_processed("outputImage")
		return img
	
	def get_output_text(self):
		img = self.P.get("output_Text")
		self.P.parameter_processed("output_Text")
		return img
	
	def updating(self, updating = None):
		if updating == None: #Not setting it, just requesting if the updating the buffer 
			return self.is_updating
		if updating == True or updating == False: #Set the buffer to updating
			self.is_updating = updating
			return self.is_updating
		return self.is_updating

	def processing(self, processing = None):
		if processing == None: #Not setting it, just requesting if the updating the buffer 
			return self.is_processing
		if processing == True or processing == False: #Set the buffer to updating
			self.is_processing = processing
		return self.is_processing