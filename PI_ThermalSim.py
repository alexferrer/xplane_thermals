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
from thermal_model import DrawThermal
from thermal_model import DrawThermalMap

from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *

from random import randrange
import math

#for graphics
from XPLMDisplay import *
from XPLMScenery import *
from XPLMGraphics import * 

#for menus
from XPLMMenus import *
toggleThermal = 1
randomThermal = 2


class PythonInterface:
    def XPluginStart(self):
        global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl
        
        global myMenu
        mySubMenuItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "Python - Thermals 1", 0, 1)
        self.MyMenuHandlerCB = self.MyMenuHandlerCallback
        self.myMenu = XPLMCreateMenu(self, "Thremals1", XPLMFindPluginsMenu(), mySubMenuItem, self.MyMenuHandlerCB,   0)
        XPLMAppendMenuItem(self.myMenu, "Toggle thermal visibility", toggleThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Random Thermals", randomThermal, 1)
        
        
        
        
        
        self.Name = "ThermalSim2"
        self.Sig =  "AlexFerrer.Python.ThermalSim2"
        self.Desc = "A plugin that simulates thermals (beta)"

        """ Data refs we want to record."""
        # airplane current flight info
        self.PlaneLat  = XPLMFindDataRef("sim/flightmodel/position/latitude")
        self.PlaneLon  = XPLMFindDataRef("sim/flightmodel/position/longitude")
        self.PlaneElev = XPLMFindDataRef("sim/flightmodel/position/elevation")
        self.PlaneHdg  = XPLMFindDataRef("sim/flightmodel/position/psi") #plane heading
        self.PlaneRol  = XPLMFindDataRef("sim/flightmodel/position/phi") #plane roll
        
        self.WindSpeed = XPLMFindDataRef("sim/weather/wind_speed_kt[0]") #wind speed at surface
        self.WindDir   = XPLMFindDataRef("sim/weather/wind_direction_degt[0]") #wind direction
        self.WindFlag  = True
        
        # variables to inject energy to the plane 
        self.lift = EasyDref('sim/flightmodel/forces/fnrml_plug_acf', 'float')
        self.roll = EasyDref('sim/flightmodel/forces/L_plug_acf', 'float') # wing roll     
        # although lift should be enough, some energy has to go as thrust, or the plane
        # might float in the air without moving!
        self.thrust  = EasyDref('sim/flightmodel/forces/faxil_plug_acf', 'float')

           
        # make a random thermal_model(size,# of thermals) 
        self.thermal_map = MakeThermalModel(1000,25,200) #size,quantity,diameter
        # image to mark thermals
        self.ObjectPath = "lib/dynamic/balloon.obj" 
        
        self.locations = DrawThermalMap(self.thermal_map) 

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
        
        # build object list for drawing
        if self.WindFlag :
           self.locations = DrawThermalMap(self.thermal_map)   #the locations where to draw the objects..
           self.WindFlag = False
           
        locations = self.locations
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
        wind_speed = XPLMGetDataf(self.WindSpeed)*0.5144 #Knots to m/s
        wind_dir = XPLMGetDataf(self.WindDir)

        if [wind_speed,wind_dir] <>  self.thermal_map[0][2] :
            self.thermal_map[0][2] = [wind_speed,wind_dir]  #insert wind vector into matrix 
            self.WindFlag = True
            print "a wind change has happened",wind_speed,wind_dir
        
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

    def MyMenuHandlerCallback(self, inMenuRef, inItemRef):
            if (inItemRef == toggleThermal):
                print " you pressed toggle thermal"
            
            if (inItemRef == randomThermal):
                print "you pressed random Thermal"
                pass        
