"""
Thermal simulator
version .01
  randomly add lift/sink/roll forces to a plane
"""
from XPLMDefs import *
from EasyDref import EasyDref

#thermal modeling tools
from thermal_model import make_thermal_model

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
		
		#have thermal_model make us a random thermal_model(size,# of thermals) 
		self.thermal_map = make_thermal_model(1000,100)


		""" Find the data refs we want to record."""
		self.PlaneLat = XPLMFindDataRef("sim/flightmodel/position/latitude")
		self.PlaneLon = XPLMFindDataRef("sim/flightmodel/position/longitude")
		self.PlaneEl = XPLMFindDataRef("sim/flightmodel/position/elevation")
		
		#For X-Plane 9 and below us vert speed (m/s)
		#self.lift = EasyDref('sim/flightmodel/position/local_vy', 'float')
		
		#For X-Plane 10 only 
		self.lift  = EasyDref('sim/flightmodel/forces/fnrml_plug_acf', 'float')
		self.roll  = EasyDref('sim/flightmodel/forces/L_plug_acf', 'float') # wing roll 
		
		#although lift should be enough, some energy has to go as thrust, or the plane
		# might float in the air without moving!
		self.thrust  = EasyDref('sim/flightmodel/forces/faxil_plug_acf', 'float')

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
		in space by using the x digits of lat/lon as index on a 
		2dimensional array representing space (lat,lon) 
		the value representing lift/sink (+/-) 
		b = [ [[11,12],[13,14]] , [[21,22],[23,24]] ]
		"""
		 
		'''
		 for lat/lon, 12.3456789
		 .1     = 11,120 meters
		 .01    =  1,120 m
		 .001   =    120 m
		 .0001  =     11 m
		 .00001 =      1 m
		 
		 a matrix of [100,100] on a .0001 (11m resolution) represents 1.1km^2
		 
		'''
		# use 2nd,3rd,4rd decimal of the lat/lon nn.x123 (blocks of 11 meters) as the key
		# on a [1000x1000] matrix = 10km^2 that repeats every 11km as the .1 digit changes
		
		#bug: will fail when - sign is not present in lat/lon, later change to abs(lat)
		#     might fail when lon > 99 because of extra digit
		thermal_value = self.thermal_map[int(str(lat)[5:8])][int(str(lon)[5:8])] 
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
		#self.lift.value  = lift_val/2 
        
		# On xplane 10.30+ you can add arbitrarly forces in newtons of force
		
		# 1kilo weights ~ 1 newton (9.8) newton               
		# ask21 (360kg) + pilot (80) = = 440kg, 
		# lift 440kg 1/ms = ~ 4400 newtons ?
		l1 = self.lift.value  #old value
		#according to Ask21 manual at 70mph sink is 1m/s
		# multiplication factor, calculated experimentally = 500
		lift_val = 5
		l2 = lift_val * 500   
		self.lift.value = l1 + l2 
		
		#although extra lift is what should be happening, 
		#adding thrust works much better! -150 = 1m/s
		tval = self.thrust.value
		self.thrust.value = -100 * lift_val + tval
		
		roll_val = 0
		#self.roll.value = roll_val


		#print "lift > ",lat,str(lat)[5:8],"  |  ",lon,str(lon)[5:8], lift_val
		print "lift > ",str(lat)[5:8]," | ",str(lon)[5:8], lift_val
        
		# set the next callback time in +n for # of seconds and -n for # of Frames
		return .01 # works on my machine..
		
