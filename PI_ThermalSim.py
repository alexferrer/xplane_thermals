"""
Thermal simulator
version .01
   randomly add lift/sink/roll forces to a plane
"""
from XPLMDefs import *
from EasyDref import EasyDref

from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *

from random import randrange


class PythonInterface:
	def XPluginStart(self):
		global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl
		self.Name = "ThermalSim2"
		self.Sig =  "SandyBarbour.Python.ThermalSim2"
		self.Desc = "A plugin that simulates thermals (alpha)"


		""" Find the data refs we want to record."""
		self.PlaneLat = XPLMFindDataRef("sim/flightmodel/position/latitude")
		self.PlaneLon = XPLMFindDataRef("sim/flightmodel/position/longitude")
		self.PlaneEl = XPLMFindDataRef("sim/flightmodel/position/elevation")
		
		#For X-Plane 9 and below us vert speed (m/s)
		self.lift = EasyDref('sim/flightmodel/position/local_vy', 'float')
		
		#For X-Plane 10 only 
		#self.lift  = EasyDref('sim/flightmodel/forces/fnrml_plug_acf', 'float')
		#self.roll  = EasyDref('sim/flightmodel/forces/L_plug_acf', 'float') # wing roll 
		
		# Use com1 as Thermal index indicator  
		self.com1  = EasyDref('sim/cockpit/radios/com1_freq_hz', 'int') 

		"""
		Register our callback for once a second.  Positive intervals
		are in seconds, negative are the negative of sim frames.  Zero
		registers but does not schedule a callback for time.
		"""
		self.FlightLoopCB = self.FlightLoopCallback
		XPLMRegisterFlightLoopCallback(self, self.FlightLoopCB, 1.0, 0)
		return self.Name, self.Sig, self.Desc

	def XPluginStop(self):
		# Unregister the callback
		XPLMUnregisterFlightLoopCallback(self, self.FlightLoopCB, 0)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass
		
	def CalcThermal(self,lat,lon,alt):
		"""
		Calculate the strenght of the thermal at this particular point 
		in space
		For now , just a simple algorithm 
		for lat 
		   .0          = 10
		   .1 or .9    = 9
		   .2 or .8    = 8 
		   and so on
		   .5          = 0
		"""
		
		"""
		a 3-dimensional array representing space (lat,lon,alt) 
		the value representing lift/sink (+/-) 
		b = [ [[11,12],[13,14]] , [[21,22],[23,24]] ]
		"""
		
		#for now:
		
		#2-dimensional array  (Grid of aprox 1km X 1km ) 
		thermal_map = [ [ 0,0,0,0,0,0,0,0,0,0 ], \
						[ 0,1,1,1,1,1,1,1,1,0 ], \
						[ 0,1,3,3,3,3,3,3,1,0 ], \
						[ 0,1,4,4,4,4,4,4,1,0 ], \
						[ 0,1,4,8,9,9,8,4,1,0 ], \
						[ 0,1,4,8,9,9,8,4,1,0 ], \
						[ 0,1,4,4,4,4,4,4,1,0 ], \
						[ 0,1,3,3,3,3,3,3,1,0 ], \
						[ 0,1,1,1,1,1,1,1,1,0 ], \
						[ 0,0,0,0,0,0,0,0,0,0 ], \
                      ]  		
		
		# use 3rd decimal of the latitude (blocks of ~100 meters) as the key
		thermal_value = thermal_map[int(str(lat)[6])][int(str(lon)[6])] 
		return thermal_value


	def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
		# The actual callback.  First we read the sim's time and the data.
		elapsed = XPLMGetElapsedTime()
		lat = XPLMGetDataf(self.PlaneLat)
		lon = XPLMGetDataf(self.PlaneLon)
		el = XPLMGetDataf(self.PlaneEl)
		
		
		#Get the lift value from the thermal matrix
		lift_val = self.CalcThermal(lat,lon,el)	

    #Apply the thermal effect Xplane 9.0 vert speed in m/s 1 = 200f/m
		self.lift.value  = lift_val/2 

		# On xplane 10.30+ you can add arbitrarly forces               
		
		#self.lift.value = lift_val * 2000
		roll_val = 0
		#self.roll.value = roll_val

		self.com1.value= (120+lift_val)*1000 # set the radio to the lift value as indicator onboard

		print "lift ",str(lat)[6]+str(lat)[7],str(lon)[6]+str(lon)[7], lift_val
        
		# set the next callback time in +n for # of seconds and -n for # of Frames
		return .5;
		
