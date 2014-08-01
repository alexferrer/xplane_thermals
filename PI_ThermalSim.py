"""
Thermal simulator  Ver .02  
  ** Works on Xplane 10.30 and above only **
  This plugin generates a thermal map (A 2D matrix of 1000x1000) that
  contains lift values foe every lat/lon spot.  
  
  The plugin then reads the lift value of the plane current position and applies
  the lift & roll values. 
  
  This version works, but is still unrealistic 
  
  Author: Alex Ferrer
  License: GPL 
"""
from XPLMDefs import *
from EasyDref import EasyDref

#thermal modeling tools
from thermal_model import MakeThermalModel
from thermal_model import CalcThermal

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
		self.thermal_map = MakeThermalModel(1000,25,200) #size,quantity,diameter


		""" Find the data refs we want to record."""
		# airplane current flight info
		self.PlaneLat  = XPLMFindDataRef("sim/flightmodel/position/latitude")
		self.PlaneLon  = XPLMFindDataRef("sim/flightmodel/position/longitude")
		self.PlaneElev = XPLMFindDataRef("sim/flightmodel/position/elevation")
		self.PlaneHdg  = XPLMFindDataRef("sim/flightmodel/position/psi") #plane heading
		self.PlaneRol  = XPLMFindDataRef("sim/flightmodel/position/phi") #plane roll
		
		# variables to inject energy to the plane 
		self.lift = EasyDref('sim/flightmodel/forces/fnrml_plug_acf', 'float')
		self.roll = EasyDref('sim/flightmodel/forces/L_plug_acf', 'float') # wing roll 	
		# although lift should be enough, some energy has to go as thrust, or the plane
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
		


	def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
		# instantiate the actual callbacks.  
		elapsed = XPLMGetElapsedTime()
		lat = XPLMGetDataf(self.PlaneLat)
		lon = XPLMGetDataf(self.PlaneLon)
		elevation = XPLMGetDataf(self.PlaneElev)
		heading = XPLMGetDataf(self.PlaneHdg)
		
		
		#Get the lift value of the current position from the thermal matrix
		lift_val, roll_value  = CalcThermal(self.thermal_map,lat,lon,elevation,heading)	
		
		# 1kilo weights ~ 1 newton (9.8) newton               
		# ask21 (360kg) + pilot (80) = = 440kg, 
		# lift 440kg 1/ms = ~ 4400 newtons ?
		# according to Ask21 manual at 70mph sink is 1m/s
		# multiplication factor, calculated experimentally = 500
		
		lval = lift_val * 500  + self.lift.value
		self.lift.value = lval  
		
		# although extra lift is what should be happening...
		# adding a bit of thrust works much better! -150 = 1m/s
		tval = self.thrust.value
		self.thrust.value = -100 * lift_val + tval	

		rval = roll_val * 6000 + self.roll.value
		self.roll.value = rval
        
		# set the next callback time in +n for # of seconds and -n for # of Frames
		return .01 # works good on my (pretty fast) machine..
		
