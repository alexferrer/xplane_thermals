"""
Thermal simulator  Ver .02  
  ** Works on Xplane 10.30 and above only **
  This plugin generates a thermal map (A 2D matrix of 1000x1000) that
  contains lift values foe every lat/lon spot.  
  
  The plugin then reads the lift value of the plane current position and applies
  the lift & roll values. 
  
  This version works.
  
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
import math

#for graphics
from XPLMDisplay import *
from XPLMScenery import *
from XPLMGraphics import * 


class PythonInterface:
    def XPluginStart(self):
        global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl
        self.Name = "ThermalSim2"
        self.Sig =  "AlexFerrer.Python.ThermalSim2"
        self.Desc = "A plugin that simulates thermals (beta)"
           
        #have thermal_model make us a random thermal_model(size,# of thermals) 
        self.thermal_map = MakeThermalModel(1000,25,200) #size,quantity,diameter
        
        #graphic to represent thermal marker in sky
        self.ObjectPath = "lib/dynamic/balloon.obj" 

        """ Data refs we want to record."""
        # airplane current flight info
        self.PlaneLat  = XPLMFindDataRef("sim/flightmodel/position/latitude")
        self.PlaneLon  = XPLMFindDataRef("sim/flightmodel/position/longitude")
        self.PlaneElev = XPLMFindDataRef("sim/flightmodel/position/elevation")
        self.PlaneHdg  = XPLMFindDataRef("sim/flightmodel/position/psi") #plane heading
        self.PlaneRol  = XPLMFindDataRef("sim/flightmodel/position/phi") #plane roll
        
        self.WindSpeed = XPLMFindDataRef("sim/weather/wind_speed_kt[0]") #wind speed at surface
        self.WindDir   = XPLMFindDataRef("sim/weather/wind_direction_degt[0]") #wind direction
        
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
        
        # Register Drawing callback
        self.DrawObjectCB = self.DrawObject
        XPLMRegisterDrawCallback(self, self.DrawObjectCB, xplm_Phase_Objects, 0, 0)

        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):    # Unregister the callbacks
        XPLMUnregisterFlightLoopCallback(self, self.FlightLoopCB, 0)
        XPLMUnregisterDrawCallback(self, self.DrawObjectCB, xplm_Phase_Objects, 0, 0)

    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass
        
    # Functions for graphics drawing
    def LoadObject(self, fname, ref):
        self.Object = XPLMLoadObject(fname)
     
    def DrawObject(self, inPhase, inIsBefore, inRefcon):
        self.LoadObjectCB = self.LoadObject
        XPLMLookupObjects(self, self.ObjectPath, 0, 0, self.LoadObjectCB, 0)
        lat,lon,alt = -12.3994,-76.7666,300.01
        Dew,Dud,Dns = XPLMWorldToLocal(lat,lon,alt/3.28) #Dew=E/W,Dud=Up/Down,Dns=N/S 
        location1 = [Dew,Dud,Dns, 0, 0, 0]
        
        lat,lon,alt = -12.3890,-76.7581,300.01
        Dew,Dud,Dns = XPLMWorldToLocal(lat,lon,alt/3.28) #Dew=E/W,Dud=Up/Down,Dns=N/S 
        location2 = [Dew,Dud,Dns, 0, 0, 0]

        #Dew,Dud,Dns = XPLMWorldToLocal(-12.3774,-76.7815,300.01/3.28) 
        #location3 = [Dew,Dud,Dns, 0, 0, 0]

        locations = [location1,location2] #,location3] 
                
#-----------------
        # winddrift: cut&past from thermal_model, for testing.. 
        #todo: refactor later..
        wind_speed = 5  # 5 m/s = 11 mph
        wind_dir   = math.radians(270)  # wind comming from the west
        
        for step in range(1,30):
            alt = 50 * step
            climb_time = alt/2.54           # assuming thermal raises at ~ 500ft/m
            drift = wind_speed * climb_time  
            dY = int(round(math.cos(wind_dir) * drift )) #east/west drift 
            dX = -int(round(math.sin(wind_dir) * drift )) #north/south drift
            locations.append([Dew+dX,Dud+alt,Dns+dY, 0, 0, 0])

    
#-----------------
        #print "locations "+str(len(locations))
        XPLMDrawObjects(self.Object, len(locations), locations, 0, 1)
        return 1

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        # instantiate the actual callbacks.  
        elapsed = XPLMGetElapsedTime()
        lat = XPLMGetDataf(self.PlaneLat)
        lon = XPLMGetDataf(self.PlaneLon)
        elevation = XPLMGetDataf(self.PlaneElev)
        heading = XPLMGetDataf(self.PlaneHdg)
        roll_angle = XPLMGetDataf(self.PlaneRol)
        wind_speed = XPLMGetDataf(self.WindSpeed)
        wind_dir = XPLMGetDataf(self.WindDir)
        #print "wind --->s/d ",wind_speed,wind_dir        
        #Get the lift value of the current position from the thermal matrix
        lift_val, roll_val  = CalcThermal(self.thermal_map,lat,lon,elevation,heading,roll_angle)    
        
        # 1kilo weights ~ 1 newton (9.8) newton               
        # ask21 (360kg) + pilot (80) = = 440kg, 
        # lift 440kg 1/ms = ~ 4400 newtons ?
        # according to Ask21 manual at 70mph sink is 1m/s
        # multiplication factor, calculated experimentally = 500
        
        lval = lift_val * 50  + self.lift.value  #500
        self.lift.value = lval  
        
        # although extra lift is what should be happening...
        # adding a bit of thrust works much better! -150 = 1m/s
        tval = self.thrust.value
        self.thrust.value = -80 * lift_val + tval    #100

        rval = roll_val * 3000 + self.roll.value #5000
        self.roll.value = rval
        
        # set the next callback time in +n for # of seconds and -n for # of Frames
        return .01 # works good on my (pretty fast) machine..
        
