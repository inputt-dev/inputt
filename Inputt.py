from pynput.keyboard import Key, Listener
import time
from parameters import Parameters
from guiThread import GUIThread
import numpy as np
from Globals import Globals, status
from workerthreads import threads
import math
from PIL import Image
import os
import sys
from datetime import date

class Inputt():
	#just like input, but non blocking and flags keystrokes
	def __init__(self):
		self.active = False
		self.keydown = False #If any key is being pressed
		self.lastKey = ''
		self.lines = ['start'] #Log all lines ended by an enter
		self.enterLine = False
		self.oneTouchKeys = [] #A list of characters the user can press without pressing enter to input in
		self.output = "" #Stores the string as the user types it
		self.menuItems = {} #Detail the menu structure
		self.menuLevel = [] #Start at the root menu
		self.endProgram = False #Keep running till the user escapes to the end
		self.statusVariables = {} #{"name": "value"}
		self.pressed = None
		self.functionReturn = None #After the user selects a function, this is its return value, set it back to None after its displayed
		self.menuSelections = [] #A list of all menu options available, set up by the print menu function
		self.gui = GUIThread("GUI", []) #Start running the GUI, and update it as necessary
		self.set_prompt("") #The default prompt
		self.log = ""

	def startGui(self):
		self.gui.start()

	def __str__(self):
		ret = ""
		if self.keydown:
			keydown = "key {} is being pressed".format(self.lastKey)
		else:
			keydown = "unpressed"
		if self.enterLine:
			enterLine = "Enter is pressed, user entered".format(self.output)
		else:
			enterLine = "User is still typing, current line {}".format(self.pressed)
		ret += "Inputt is active: {}. {} lines entered. Keyboard is {}\n".format(self.active, len(self.lines), keydown)
		ret += "Current menu system:\n"
		ret += self.printFullMenu()
		ret += "Currently in menu {}".format(self.menuLevel)
		return ret

	def start(self): #Start listening
		self.output = ""  #Start collecting the users input
		if self.active == True:
			return
		self.listener = Listener(on_press=self.on_press,on_release=self.on_release)
		self.listener.start() #start the keyboard listener thread
		self.active = True
	def stop(self): #Stop the listener thread
		try:
			self.active = False
			self.enterLine = False
			self.listener.stop()
		except Exception: #In case its called when the thread is already gone
			pass
	def on_press(self, key):
		#if self.keydown == True: #Want to avoid long presses for one touch processing
		#	return
		self.keydown = True
		if key == Key.enter:
			#Check if this is a menu selection
			if self.output in self.menuSelections:
				self.menuLevel.append(self.output)	#Advance into this menu option
			self.lines.append(self.output)
			self.output = ""
			self.enterLine = True #Flag a line of input is ready, flip it back once processed
			return
		elif key == Key.esc:
			self.output = "Escape"
			self.enterLine = True
			self.lines.append(self.output)
			return
		elif self.oneTouchKeys == ['ALL']:
			try:
				key = key.char
			except:
				pass #Try to convert to character, or just pass on the Key.whatever
			self.output = key
			self.lines.append(self.output)
			self.output = ""
			self.enterLine = True
			return
		elif key == Key.backspace:
			if self.output == "":
				return #Dont backspace no input, it'll erase things off the field of input
			self.output = self.output[:-1] #chop off the end of the output string
			print("\b \b", end = "") #Backspace erase and backspace again to reset the cursor
			self.updatePrompt(self.output)
			return
		#Now lets separate alphanumeric keys from others
		try:
			self.output += key.char
			print(key.char, end = "") #Echo the keypress
			self.updatePrompt(self.output)
		except Exception as e:
			if key == Key.left:
				self.output = "<-"
			elif key == Key.right:
				self.output = "->"

		#Now check if this keypress is a one touch key
		if self.output in self.oneTouchKeys:
			self.lines.append(self.output) #Store it as a line the history list
			self.enterLine = True
			#advance the menu option one level in
			self.menuLevel.append(self.output)	#Need to appened menu levels even if its not a one touch key
		self.lastKey = key
	def on_release(self, key):
		self.keydown = False

	def printFullMenu(self):  #Output the whole menu system
		ret = ""
		for menu, text in self.menuItems.items():
			menu = list(menu) #Bc we cant hash lists so the dictionary needs this converted
			name = text[0]
			ret += "{}. {}\n".format(menu, name)
		return ret
	def getTitle(self):
		#Return the title of the current menu level
		ret = self.menuItems[tuple(self.menuLevel)][0]
		return ret
	def updateMenuItem(self, menuPath, message):
		try:
			func = self.menuItems[tuple(menuPath)][1]
			self.menuItems[tuple(menuPath)] = (message, func)
		except Exception as e:
			print("Inputt error {}".format(e))
			print(self)		
	def add_menu_item(self, id, name, func):
		#id = menu index, ie 1. or 1.1, 4.1, 4.2 etc
		#1. Option 1 = [1]
		#2. heading 1 = [2]
		#   2.1 Option 2 = [2,1]
		#   2.2 Option 3 = [2,2]
		#   2.3 Heading 2 = [2,3]
		#      2.3.1 Option 4 = [2,3,1]
		#      2.3.2 Option 5 = [2,3,2]
		#3. Option 6 = [3]
		#4. Heading 3 = [4]
		#   4.1 Option 7 = [4,1]
		#   4.2 Option 8 = [4,2]
		#   4.3 Heading 4 = [4,3]
		#      4.3.1 Option 9 = [4,3,1]
		#and so on 
		typer = str(type(name))
		if typer == "<class 'numpy.ndarray'>": #change it to a PIL image
			name = Image.fromarray(name)
		self.menuItems[tuple(id)] = (name, func)
	def deleteMenuPath(self, menuPath):
		#First remove the any current options on this menu path
		for k in list(self.menuItems.keys()):
			#Check if the menu path is the root menu of this menu option
			if len(k) == len(menuPath) +  1:
				#Assume match is true,only set it false when known for sure
				match = True
				#Its the right length for menuPath to be the root menu
				for index, mp in enumerate(menuPath):
					if mp == k[index]: #Match letter by letter
						continue
					else: #No match
						match = False
						break
				if match == True:
					#If this menu option is one level from the menuPath, remove it for adding later
					del self.menuItems[k]

	def enumerationSelection(self, x):
		return lambda : [x]  #Return the item selected
	def enumerateAndSelect(self, items): #process function points to the function to executed when the user makes their selection
		self.gui.updatingBuffer(bufferUpdating = True) #Set the drawing and buffer locks
		self.deleteMenuPath(self.menuLevel) #Clear the menu options below it must be dynamic
		self.oneTouchKeys = [] #We'll remake the list while dynamically creating the menu entry
		#self.gui.clearText() #Prep the screen for new things

		typer = str(type(items)) #Multiple data types can be enumerated, but lets make one function to handle them all
		#first make the selection names based on the object type
		if typer == "<class 'parameters.Parameters'>":
			#Make a list off all the items in the parameter object
			ParametersList = items.toList()
			for index, i in enumerate(ParametersList, 1):
				added = self.menuLevel.copy()
				added.append(str(index)) #Make the new, dynamic menu entry, starting at 1
				name = str(i)
				func = self.enumerationSelection(str(items.get(ParametersList[index - 1]))) #This is in a list going into another list FIX
				self.add_menu_item(added, name, func)

		if typer == "<class 'dict'>":
			rowcount = 0
			for index, (key, val) in enumerate(items.items(),1):
				added = self.menuLevel.copy()
				#name = items[key]
				added.append(str(index)) #Make the new, dynamic menu entry, starting at 1
				func = self.enumerationSelection(key)
				menuText = "{}".format(key)
				self.add_menu_item(added, menuText, func)
				indent = len(menuText) + 3
				line_number = rowcount
				rowcount += self.gui.addToBuffer(indent, line_number, val)

		if typer == "<class 'list'>":
			rowcount = 1 #Add one for the top row showing the menu title
			for index, i in enumerate(items, 1):
				added = self.menuLevel.copy()
				added.append(str(index)) #Make the new, dynamic menu entry, starting at 1
				name = items[index - 1] #Because we started from 1 but lists start from zero
				rowcount += self.gui.addToBuffer(0,rowcount,i)
				func = self.enumerationSelection(i)
				self.add_menu_item(added, name, func)

		self.enterLine = False
		self.output = "" #Prep the indicator variables to accept new input and prepare to select from the list
		self.print_menu() #Display it and set one touch keys, if less than 10 items being displayed
		title = self.getTitle()
		self.gui.setOutputPane(["Viewing {}".format(title), "Enunmeration selection {}".format(self.menuLevel)])
		#self.gui.updatingBuffer(False) #We know this thread is done updating the buffer
		selection = self.next_line() #And then get the users selection
		ret = self.outputt()[0] #Because outputt always returns a list for drawing to the output section
		return ret

	def goUpOneLevel(self):
		if self.menuLevel == []: #Were at the root menu
			self.endProgram = True
			return
		self.menuLevel = self.menuLevel[:-1] #Go up one level
	
	def Escape(self): #The all important escape key, go up one menu level for everything, defined in inputt
		self.goUpOneLevel()
		ret = [False]
		#Need to check the menu level and activate outputvisual for running threads, if we go to the level that spawned the thread
		return ret
	
	def print_menu(self): 
		#Prints the menu and calculates metrics like selection options and screen size while doing it
		self.gui.updatingBuffer(bufferUpdating = True) #Set the drawing and buffer locks
		self.gui.clearText()
		escapeOption = self.menuLevel.copy()
		escapeOption.append("Escape") #So hitting the Escape key brings us one menu level, escaping up
		self.add_menu_item(escapeOption,"Go up one level", self.Escape) #Put in the 
		oneTouchCount = 0 #If its above 10 we need to cancel one touch keys
		y = 1 #Top row is for menu id status, count the rows needed to display the menu
		title = str(self.menuLevel) + ": " + str(self.menuItems[tuple(self.menuLevel)][0]) #Level: Level's name
		x = int((self.gui.numberOfColumns - len(title))/2)
		self.gui.addToBuffer(x,0,title)
		#Count the size of the printed menu and resize it for the printed menu
		nameLength = 80
		#Calculate the size of the menu and prompt
		current_row_height = 1 #Increase for the height of the image
		#Clear the menu selection lists for this new menu
		self.oneTouchKeys = [] #If less than 10, do one touches, 
		self.menuSelections = [] #But still need to know what the selection options are
		for menu, text in self.menuItems.items():
			menu = list(menu) #Bc we cant hash lists so the dictionary needs this converted
			menuPath = menu[0:-1] #The path is everything except the last element the user selects as a onetouchkey
			if menuPath == self.menuLevel:
				try:
					menuOneTouch = menu[-1] #Select the one touch key menu option and the previous one touch key
				except Exception as e:
					continue
				name = text[0] #Check for row height
				typer = str(type(name))
				if typer == "<class 'numpy.ndarray'>":
					i = Image.fromarray(i)
					typer =  str(type(i))
				elif typer == "<class 'PIL.Image.Image'>": #Its an image
					size = name.size
					y += 2 #Because Im using thumbnails defined as twice row size for menu selection
				else: #Its a string or something else that will be converted to a string
					name = str(name)
					y += 1
					
				nameLength = max(len(name),nameLength) #Keep a running track of the columns in case we need to expand the window
		#if y > self.gui.numberOfRows or nameLength > self.gui.numberOfColumns:
		self.gui.divideLineInputVOutput = y + 2 #To maximize screen space for output, start output right beneath the input&prompt
		self.gui.resize(nameLength, self.gui.divideLineInputVOutput)

		#Add the items in the menu and prompt to the gui
		y=1
		for menu, text in self.menuItems.items():
			menu = list(menu) #Bc we cant hash lists so the dictionary needs this converted
			menuPath = menu[0:-1] #The path is everything except the first element
			if menuPath == self.menuLevel:
				try:
					menuOneTouch = menu[-1] #Select the one touch key menu option and the previous one touch key
				except Exception as e:
					continue
				name = text[0] #Check for row height
				text = "{}. {}".format(menuOneTouch, name)
				nameLength = max(len(text),80)
				print(text)
				#Add it to the CLI GUI as well as printing it
				typer = str(type(name))
				if typer == "<class 'PIL.Image.Image'>": #Its an image
					maxSize = self.gui.getImageThumbnailSize()
					name.thumbnail(maxSize)
					self.gui.addToBuffer(0,y, menuOneTouch + ". ")
					y += self.gui.addToBuffer(5,y, name)
				else:
					y += self.gui.addToBuffer(0, y, text) #add the text or image

				self.oneTouchKeys.append(menuOneTouch)
				self.menuSelections.append(menuOneTouch) #This list stays, onetouch disappears over 10 selection options
				oneTouchCount += 1 
	
		if oneTouchCount > 10: #Cant type 16 for instance without onetouching 1 first so we need to disable it
			self.oneTouchKeys = []
		#Add the prompt to the buffer
		#self.gui.addToBuffer(0, y + 1, "Select Option(1-{})".format(oneTouchCount))
		self.set_prompt("Select Option(1-{})".format(oneTouchCount))
		print(self.promptText)
		self.gui.updatingBuffer(False) #Done writing the menu
		
	def stop_threads(self):
		#Shut down the running threads
		runningThreads = threads.iterable()
		for rt in runningThreads:
			rt.stop()


	def outputt(self):
		self.gui.updatingBuffer(bufferUpdating = True) #Set the drawing and buffer locks
		#Lets get the last line entered by the user
		lastLineEntered = self.lines[-1]
		#Lets get the menuItem the user has selected
		menuItem = self.menuItems[tuple(self.menuLevel)]

		#Lets process the user input
		name = menuItem[0] #unpack the tuple
		func = menuItem[1]

		#Do the escape function if escape is pressed, later try to handle this automatically as part of the function execution
		if lastLineEntered == "Escape":
			func = self.Escape

		if func != None: #run the function if supplied
			self.functionReturn = func()
			#Clear the screen to put in the new output and prep it for the next menu printing
			while self.gui.drawingScreen():
				pass
			self.gui.clearText() #Prep the text array for a new set of characters
			self.print_menu() #Add the menu into the buffer array
			#Set the window size based on the output size and write in the output from the menu function
			self.gui.setOutputPane(self.functionReturn)
		self.enterLine = False	#Get ready for a next_line
		self.gui.updatingBuffer(False) #Open for screen drawing now
		return self.functionReturn #True if a function ran, false otherwise
	
	def next_line(self): #returns a string the user typed or false if still checking
		#Flag the prompt to draw the gui screen
		if self.enterLine: #The enter key was pressed, get the last line recorded
			return self.lines[-1]
		self.start() #Start listening for keystrokes
		#Lets see if any running thread started from this current menu level, if so show the the threads output in the output pane
		images = []
		displayThread = False #Presume no thread to displaynd
		for rt in threads.iterable():
			threadMenuLevel = rt.P.get("Menu Level")
			if threadMenuLevel == self.menuLevel:
				displayThread = rt #We have a thread created at this menu level, we will display it in the output pane
			

		#This loop waits for a line to be entered by the user, while its waiting if theres an active thread at this menu
		#level it will display its output, either an image or text if no image is available
		print("> ", end="")
		db = Globals.get("db")
		update_menu = False
		thread_output = []
		while self.enterLine == False: #Wait for the user to type a selection
			if displayThread:
				if displayThread.P.isUpdated("outputImage"):
					img = displayThread.getOutputImage()
					thread_output = ["Thread {}".format(displayThread), img]
					update_menu = True
				elif displayThread.P.isUpdated("output_Text"):
					text = displayThread.get_output_text()
					thread_output = [text]
					update_menu = True

			if update_menu:
				status()	
				self.print_menu() #Add the menu into the buffer array
				self.gui.setOutputPane(thread_output)

			thread_output = []
			update_menu = False
		print("")
		self.stop() #Turn off the listener
		return self.lines[-1] #Otherwise nothing
		
	def getFileName(self, default, ext = ""): #Gets a filename from the user, using enter to select the default string
		#Get the files from the current path
		Root_Path = globals.get("Root Path")
		items = os.listdir(Root_Path)

		fileList = []

		for name in items: #Peel off the files with the extension
			if name.endswith(ext):
				fileList.append(name)
		#select one of the files
		for cnt, fileName in enumerate(fileList, 1):
			sys.stdout.write("[%d] %s\n\r" % (cnt, fileName))
		
		fileSelected = self.enumerateAndSelect(fileList)
		fileSelected = Root_Path + fileSelected[0]
		return fileSelected

	def getString(self, promptText, default):
		self.updatePrompt(f'promptText + ({default})')
		ret = self.next_line()
		if ret == "":
			ret = default
		return ret
	
	def getColor(self, defaults):
		(dR,dG,dB) = defaults
		red = self.getInteger("red value", 0, 255, dR)
		green = self.getInteger("green value", 0, 255, dG)
		blue = self.getInteger("blue value", 0, 255, dB)
		return (red, green, blue)
	def getInteger(self, promptText, min, max, current):
		invalid = True
		ret = None
		self.oneTouchKeys = []
		self.output = ""
		self.print_menu()
		while invalid:
			self.set_prompt("{}({}). {}-{}".format(promptText,current, min, max))
			userInput = self.next_line()
			try:
				ret = int(userInput)
				if ret < min:
					self.set_prompt("{} too low, minimum {}".format(ret, min))
				elif ret > max:
					self.set_prompt("{} too high, maximum {}".format(ret, max))
				else:
					invalid = False
			except Exception as e:
				if userInput == 'Escape':
					ret = False
					invalid = False
				self.set_prompt("{} is not an integer.".format(userInput))
		self.set_prompt("")
		return ret
	
	def get_date(self, promptText, min, max, current):
		invalid = True
		ret = None
		min_month = 1
		max_month = 12
		min_year = min.year
		max_year = max.year
		min_day = 1
		max_day = 31
		day = self.getInteger(f"Enter Day {min_day} - {max_day}", min_day, max_day,1)
		if day:
			month = self.getInteger(f"Enter Month {min_month} - {max_month}", min_month, max_month, 1)
			if month:
				year = self.getInteger(f"Enter Year {min_year} - {max_year}", min_year, max_year, min_year)
				if year:
					ret = date(year,month,day)
				else:
					ret = False
			else:
				ret = False
		else:
			ret = False
		return ret
			
	#Change the prompt and user input
	def set_prompt(self, promptText):
		self.promptText = promptText + "> "
		self.updatePrompt("")

	def updatePrompt(self, text):
		while self.gui.drawingScreen(): #Its drawing wait until its done then update the buffer and make it draw again
			pass
		self.gui.updatingBuffer(True) #Tell the gui its drawing the buffer dont do anything

		#See if self.prompttext is longer than the screen, if so, write it across enough lines to show all the text
		#Now put the text into
		# code to pad spaces in string
		padding_size = self.gui.numberOfColumns
		res = self.promptText + text +" "*(padding_size - len(self.promptText + text))
		promptRow = self.gui.divideLineInputVOutput - 1
		self.gui.addToBuffer(0, promptRow, res)
		self.gui.updatingBuffer(False) #No longer updating, the GUI thread is clear to redraw the screen

	def confirmAction(self, confirmText):
		self.updatePrompt("Press Enter to confirm {}".format(confirmText))
		line = self.next_line()
		if line == "":
			return True
		return False

	def shutdown(self): #Shut down the input/output threads
		self.gui.stop()
		self.stop()

	def anyKey(self, message):
		self.oneTouchKeys = ['ALL'] #A little flag to let the key press processory know to return a line with any key press
		if message == None:
			self.updatePrompt("Press any key to continue")
		else:
			self.updatePrompt(message)
		anykey = self.next_line()
		self.oneTouchKeys = [] #Reset them so it doesnt keep doing anykey
		return anykey #Might be useful to know which key was pressed
	
	def clearImage(self):
		self.gui.clearImages()

	def getlastOutput(self):
		return self.gui.outputList
	
	def log(self, entry):
		self.log += entry + "\n"
	

