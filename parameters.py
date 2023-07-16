"""
Every real world object modeled in this program is defined by a series of attributes and values.  This class creates an easy way to add and manage these
attributes, without created hand tailored code to modify and set it, the variable name is fed into the class and it exposes an interface
to change, record, validate input

Change to a pandas dataframe, for each parameters, parameters.
"""
import pandas as pd

class Parameters(): #Holds values that define the dimensions and properties of anything, allows updates and saves old values
	def __init__(self, dict):
		self.p = dict
		self.iterableIndex = 0 #For the iterable function

	def __str__(self):
		line = ""
		#list each attribute, its value and description if available
		for name, values in self.p.items():
			desc = values[1]
			value = values[0]
			updated = values[2] #We're updating the Parameter attribute
			line += "{}({}) : {}. Updated = {}\n".format(name,desc,value, updated)
		return line
	def __len__(self):
		return len(self.p)
		
	def set(self, attribute, value):
		try:
			existing = self.p[attribute]
			desc = existing[1] #get the description
			self.p[attribute] = (value, desc, True)
		except KeyError:
			parameterType = str(type(value))
			if parameterType == "<class 'tuple'>":
				self.p[attribute] = (value[0],value[1],True)
			else:
				self.p[attribute] = (value, "No Description", False)
		
	def delete(self, attribute):
		try:
			del self.p[attribute]
		except Exception:
			pass

	def setDescription(self, attribute, description):
		try:
			existing = self.p[attribute]
			value = existing[0]
			isUpdated = existing[2]
			self.p[attribute] = (value, description, isUpdated)
		except KeyError:
			parameterType = str(type(value))
			if parameterType == "<class 'tuple'>":
				self.p[attribute] = (value[0], value[1], value[2])
			else:
				self.p[attribute] = (value, description, True)

	def get(self, key):
		try:
			ret = self.p[key]
			#Change the updated parameter to False, assuming that if we get this parameter, it is being processed
			value = ret[0]
			desc = ret[1]
			self.p[key] = (value,desc,False)
			ret = value
		except KeyError:
			return None
		return ret

	def addTo(self, attribute, value): #When the value of the attribute is a list
		try:
			self.variable[attribute].append(value)
		except KeyError:
			print("{} not in the dictionary. Nothing changed".format(attribute))
		except Exception:
			print("Exception encountered add to variable list attribute")
			
	def toCSV(self):
		ret = ""
		for k,v in self.p.items():
			ret += "{}[{}],".format(k, v[1])
		ret += "\n"
		for k,v in self.p.items():
			ret += "{},".format(v[0])
		ret += "\n"

	def toCSVHeader(self): #REturn a line with the variable names with description separated by commas
		ret = ""
		for k,v in self.p.items():
			ret += "{}[{}],".format(k, v[1])
		ret += "\n"
		return ret

	def toCSVData(self): #Return all the elements in the dictionary values comma separated
		ret = ""
		for k,v in self.p.items():
			ret += "{},".format(v[0])
		ret += "\n"
		return ret

	def iterable(self): #generator function to yield a list of the values only not the dictionary or the extra information in the tuple
		for name, values in self.p.items():
			if values[0] is not None:
				yield values[0]

	def iterable_keys(self): #generator function to yield the keys
		for name, values in self.p.items():
			if values[0] is not None:
				yield values[0]

	def toList(self): #Return a list of all the items in the Parameters
		ret = []
		for name, values in self.p.items():
			ret.append(name)
		return ret
	
	def isUpdated(self, key):
		try:
			ret = self.p[key][2]
		except:
			ret = False
		return ret
	
	def isAnyUpdated(self):
		for (name, value) in self.p:
			if self.isUpdated(name):
				return True
		return False
	
	def parameter_processed(self, key):
		try:
			self.p[key][2] = False
			ret = True
		except:
			ret = False
		return ret		

	def to_tuple(self):
		ret = []
		for name, values in self.p.items():
			desc = values[1]
			value = values[0]
			ret.append(value)

		ret = tuple(ret)
		return ret
