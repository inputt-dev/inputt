from workerthreads import workerThread
import pandas as pd
import sqlite3
import random

"""
DBThread

Receive SQL commands from other threads, store them in a list and run them in one thread
Enter a SQL command receive an index for the completed command
"""
class DB():
	def __init__(self, *args, **kwargs):
		self.commands = [] #[sql command]
		self.results = {} #{index: return result}
		self.commands_Completed = 0
		self.DB_File_Path = args[0]
		self.running = True
		self.waiting_cycles = 0
		self.update_buffer = {}
		self.is_processing = False
		self.is_updating = False

	def __str__(self):
		if self.stopped():
			ret = "DB thread is OFF\n"
		else:
			ret = "DB thread running. {}/{} commands run".format(self.commands_Completed, len(self.commands))
		return ret

	#Add the sql command and its arguments to the command queue and return the index for accessing it later
	#Start the database thread if its not on already, if it is on its processing commands already
	def addCommand(self, sql, values = None):
		while self.processing():
			pass  #Wait for processing to finish
		
		self.commands.append((sql, values))
		return len(self.commands) - 1
	
	#Get the result of the sql command via index number, but may need to wait until its available.
	def result(self, index):
		while self.commands_Completed < index:
			pass
		ret = self.results[index]
		del self.results[index]
		return ret

	#Start the database and run the SQL commands
	#Store the results in self.results dictionary
	def flush_command_buffer(self):
		if len(self.commands) == 0:
			return
		self.processing(True)
		db = sqlite3.connect(self.DB_File_Path)
		for (sql_query,values) in self.commands:
			type = sql_query.split(" ")[0]
			if type == "SELECT":
				df = pd.read_sql_query(sql_query, db)
			elif type == "INSERT" or type == "UPDATE":
				df = db.execute(sql_query, values)
				df = values
			self.results.update({self.commands_Completed:df})
			print("{}:{}{} {}".format(self.commands_Completed, sql_query,values, df))
			self.commands_Completed += 1
		self.commands = []
		db.commit()
		db.close()
		self.processing(False)
	
	def select_all(self):
		index = self.addCommand("SELECT * FROM TEST")
		return self.result(index)
	
	#Returns random values for the test table
	def generate_random_record(self):
		id = random.randrange(0, 65536)
		text_length = random.randrange(4,16)
		choices = ['g','h','t','c']
		name = ""
		counter = 0
		while counter < text_length:
			name += random.choices(choices)[0]
			counter +=1
		blob_length = random.randrange(5,25)
		blob = random.randbytes(blob_length)
		value = random.random()
		values = (id, name,blob,value)
		return values
	
	def get_random_record(self):
		sql = "SELECT * FROM TEST ORDER BY RANDOM() LIMIT 1 "
		result_index = self.addCommand(sql)
		df = self.get_result(result_index)
		t= tuple(df.itertuples(index=False, name=None))
		values = t[0]
		return values
	
	#Get the result with an index to the results dictionary
	#Flush the buffer first to get any select results in there and then return it
	def get_result(self, index):
		self.flush_command_buffer()
		try:
			df = self.results[index]
		except Exception as e:
			print(e)
			df = None
		return df
	
	def processing(self, processing = None):
		if processing == None: #Not setting it, just requesting if the updating the buffer 
			return self.is_processing
		if processing == True or processing == False: #Set the buffer to updating
			self.is_processing = processing
		return self.is_processing

