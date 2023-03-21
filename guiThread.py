import threading
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import datetime
import cv2
from workerthreads import workerThread, threads
import time
import math 
import string
"""
-----------------
|options        |
|               |
|               |
|               |
-----------------
|Output         |
|               |
|               |
-----------------

text in the big portion
below is an output section, or set to monitor 
"""
class GUIThread(workerThread): #Run the gui in a separate thread
	def __init__(self, *args, **kwargs):
		super(GUIThread, self).__init__(*args, **kwargs)
		columns = 80
		rows = 25
		self._stop = threading.Event()
		self.running = True
		self.bg_color = (0,0,0)
		self.fg_color = (255,255,255)
		self.numberOfColumns = columns
		self.numberOfRows = rows
		self.divideLineInputVOutput = rows #We'll start the division between inputt&prompt from output to be the initial row size with output to put under it
		#self.resolution = (self.font_size * self.numberOfColumns,self.font_size * self.numberOfRows)
		#self.img = Image.new("RGB", self.resolution, color = (67,98,122))
		self.setFontSize(19)
		self.resize(80,25)
		self.screenRefreshes = 0
		curr_dt = datetime.datetime.now()
		timeStamp = int(round(curr_dt.timestamp()))
		self.startTime = timeStamp - 1
		self.text_color = (0,0,255)
		self.updateScreen = False
		#Maintain a list of images that are to be pasted ontop of the text
		self.images = {} # {(x,y):numpy image}
		self.drawLock = False #If the buffer is being updated, block the thread from drawing the screen until its done
		self.name = "GUI Thread"
		self.bufferUpdated = False #True if theres new info in the text buffer, False if nothings changed so dont redraw the screen  even if the buffer isnt updating
		self.outputDimensions = (0,0) #The size of the output the last executed function gave
		self.bufferUpdating = False #Were not updating the buffer right now
		self.screenDrawing = False #We're not drawing the screen right nowpa
		self.waitingCycles = 0 #Count how many buffer updates are sent while the screen is drawing
		self.bufferUpdates = {} #buffer the text buffer for updates while its drawing the screen
		self.minimum_Width = 80 #The mininum number of columns

	def setOutputPane(self, items):
		if items == []: #No input means just the menu is printing
			self.resize(self.numberOfColumns,self.divideLineInputVOutput)
			return

		self.updatingBuffer(bufferUpdating = True) #Set the drawing and buffer locks
		countOfColumns = self.numberOfColumns
		countOfRows = self.divideLineInputVOutput #The current height of the input pane

		for (index, i) in enumerate(items):
			typer = str(type(i))
			if typer == "<class 'tuple'>": #change a group to a string
				i = str(i)
				typer = "<class 'str'>"
			if typer == "<class 'str'>":
				#Count how many lines it goes down and its max line length
				lines = 1 #Must be at least this one string
				width = 0 #Length of the longest line
				current_width = 0 #Length of the line being measured
				for c in list(i):
					if c == "\n": #newline
						lines += 1
						current_width = 0
					else: #
						current_width += 1
						countOfColumns = max(countOfColumns, current_width) #Dynamically size the output pane to hold everything supplied in the list
				countOfRows += lines
				countOfColumns = max(countOfColumns, current_width)
			if typer == "<class 'numpy.ndarray'>": #Convert numpy image array from cv2 to PIL image
				i = Image.fromarray(i)
				typer =  str(type(i))
				#Now replace this element
				items[index] = i
			if typer == "<class 'PIL.Image.Image'>": #Its an image
				size = i.size
				x = math.ceil(size[0] / self.font_size)
				y = math.ceil(size[1] / self.font_size)
				countOfColumns = max(x, countOfColumns)
				countOfRows += y

			#Now we have the dimensions of the output window lets add it to the size

		self.resize(countOfColumns,countOfRows)
		#Now draw the output portion at the bottom, run through the list of output items, print out the text
		#tile the images across, adjust the size of the output window to show it all
		#First calculate the dimensions that the output pane needs
		rowCount = self.divideLineInputVOutput
		for i in items:
			rowCount += self.addToBuffer(0,rowCount,i) #Need to increment the rowCount to add the number of rows this item has

		self.outputList = items
		self.updatingBuffer(False) #Done now draw the screen

	def __str__(self):
		#ret = str(threads)
		ret = "GUIThread {}x{}x{}\n".format(self.numberOfColumns, self.numberOfRows, self.font_size)
		return ret

	def resize(self, cols, rows): #Resize the array but keep the existing data
		new_arr = np.zeros((cols,rows), dtype = (np.uint8, 7))
		#write in the old array
		for r in range(0,rows):
			for c in range(0,cols):
				try:
					new_arr[c][r] = self.screen[c][r]
				except:
					new_arr[c][r] = (0,self.fg_color[0],self.fg_color[1],self.fg_color[2],self.bg_color[0],self.bg_color[1],self.bg_color[2])
		self.screen = new_arr
		self.numberOfColumns = cols
		self.numberOfRows = rows
		self.resolution = (self.font_size * self.numberOfColumns,self.font_size * self.numberOfRows)
		self.img = Image.new("RGB", self.resolution, color = self.bg_color)

	def setFontSize(self, newSize):
		self.font_size = newSize
		self.font = ImageFont.truetype(r'.\fonts\Courier Prime\Courier Prime.ttf', self.font_size + 1)

	def clearText(self):
		self.screen = []
		self.resize(self.numberOfColumns, self.numberOfRows)
		self.images = {}
		self.bufferUpdated = True

	def drawScreen(self):
		if self.bufferUpdated == False: #Dont draw until theres something there
			return None
		if self.updatingBuffer(): #Wait for the buffer to be done updating
			return None

		self.drawingScreen(screenDrawing = True) #Set the drawing and buffer locks
		#Once the screen buffer is constructed, print it out one character at a time after going up the screen height lines
		row = 0
		column = 0
		self.img.paste( self.bg_color, [0,0,self.img.size[0],self.img.size[1]]) #Clear out the old image
		draw = ImageDraw.Draw(self.img)
		# specified font sizee
		#Print out a running fps account
		curr_dt = datetime.datetime.now()
		timeStamp = int(round(curr_dt.timestamp()))
		self.screenRefreshes += 1
		#fps = "fps {}".format(self.screenRefreshes / (timeStamp - self.startTime))
		#self.addToBuffer(self.numberOfColumns - len(fps),0,fps)
		#Print out the waiting Cycles
		#screenDraws = "Buffer updates during screen drawing: {}".format(self.waitingCycles)
		#self.addToBuffer(self.numberOfColumns - len(screenDraws),1,screenDraws)

		while row < self.numberOfRows:
			while column < self.numberOfColumns:
				pixel = tuple(self.screen[column][row])
				fg_color = '#%02x%02x%02x' % (pixel[1],pixel[2],pixel[3])
				fg_color = (255,0,0)
				bg_color = '#%02x%02x%02x' % (pixel[4],pixel[5],pixel[6])
				bg_color = (0,0,255) #b,g,r
				character = pixel[0]
				if character == 0 or character == 32:
					column +=1 
					continue
				if bg_color != self.bg_color:
					y1 = row * self.font_size
					x1 = column * self.font_size
					x2 = x1 + self.font_size
					y2 = y1 + self.font_size
					draw.rectangle((x1,y1,x2,y2), fill = bg_color)
				draw.text((x1, y1), chr(character), font = self.font, align ="center", color = fg_color)
				column +=1
			row +=1 #Advance to next row
			column = 0

		for (x,y), image in self.images.items(): #Paste in the images on this screen
			#Start pasting in the images 
			x = self.font_size * x
			y = self.font_size * y
			self.img.paste(image, (x,y))

		#return self.numpyImage
		img2 = np.array(self.img)
		self.drawingScreen(screenDrawing = False) #Open for buffer updates now
		#Now thats done, add in the buffer that may have built up
		for key,value in self.bufferUpdates.items(): #If its done drawing now add the buffered updates
			(t,a,c) = value
			self.addToBuffer(t,a,c)
		self.bufferUpdated = False #Definitely nothing new now, wait for the next keypress
		self.bufferUpdates = {}
		return img2

	def addImage(self,x,y,image):
		#as the final row number, without a number, extending the window if necessary to avoid any distortion
		#Place it in the lower rig, ht corner
		#get the dimensions in pixels of the image
		typer = str(type(image))
		if typer == "<class 'PIL.Image.Image'>":
			self.images[(x,y)] = image
		else:
			image = Image.fromarray(image)
			self.images[(x,y)] = image
		
		size = image.size
		y = math.ceil(size[1] / self.font_size)
		self.bufferUpdated = True
		return y
		
	def clearImages(self):
		self.images = {}
		self.bufferUpdated = True

	def addToBuffer(self, x, y, text, fg_color = None, bg_color = None): #Need to merge addtobuffer and addimage
		#At position x,y add the text 
		#TODO text will be a numpy array for 2d text boxes
		
		typer = str(type(text))
		while self.drawingScreen(): #Wait until its done drawing itself
			self.bufferUpdates[self.waitingCycles] = (x,y,text)
			self.waitingCycles += 1
			#Still need to return the amount of lines it would've had
			if typer == "<class 'PIL.Image.Image'>":
				size = text.size
				numLines = math.ceil(size[1] / self.font_size)
			else:
				text = str(text) #Just force everything into strings no matter what is sent to be rendered
				numLines = len(text.split("\n"))
			return numLines
		self.updatingBuffer(True) #Lets really drive home its being updated
		self.bufferUpdated = True #Flag that the buffer has updated information
		#Check if its an image, if so send it to addimage
		if text is None:
			return 0
			
		typer = str(type(text))
		if typer == "<class 'PIL.Image.Image'>":
			return self.addImage(x,y,text)
		elif typer == "<class 'numpy.ndarray'>": #Convert numpy image array from cv2 to PIL image
			i = Image.fromarray(text)
			return self.addImage(x,y,i)
		else:
			text = str(text) #If its not an image of some sort, we need it to be text
		length = len(text)
		counter = 0
		text = list(text)
		startX = x
		linesAdded = 1 #Count the number of lines added to the buffer for drawing purposes
		while counter < length:
			character = ord(text[counter])
			if character == 10:
				y += 1
				x = startX
				linesAdded += 1
			try:
				self.screen[x][y] = character
			except Exception as e:
				pass #Just in case its out of bounds 
			counter += 1
			x += 1
		return linesAdded

	# function using _stop function
	def stop(self):
		self.running = False
		self._stop.set()
 
	def stopped(self):
		return self._stop.isSet()

	def run(self):
		while self.running:
			frame = self.drawScreen()
			if frame is None:
				pass
			else:
				cv2.imshow("Inputt", frame)
			cv2.waitKey(1)
		cv2.destroyWindow("Inputt")

	def getImageThumbnailSize(self):
		ret = (self.font_size * 2, self.font_size *2) #Maybe two line max for images is nice?
		return ret

	def updatingBuffer(self, bufferUpdating = None):
		if bufferUpdating == None: #Not setting it, just requesting if the updating the buffer 
			return self.bufferUpdating
		if bufferUpdating == True or bufferUpdating == False: #Set the buffer to updating
			self.bufferUpdating = bufferUpdating
			return self.bufferUpdating
		return self.bufferUpdating

	def drawingScreen(self, screenDrawing = None):
		if screenDrawing == None: #Not setting it, just requesting if the updating the buffer 
			return self.screenDrawing
		if screenDrawing == True or screenDrawing == False: #Set the buffer to updating
			self.screenDrawing = screenDrawing
			return self.screenDrawing
		return self.screenDrawing #Bad input just output the existing value
