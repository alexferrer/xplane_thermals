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

import world

from XPLMDefs import *
from EasyDref import EasyDref

#thermal modeling tools
from thermal_model import MakeThermalModelFromList
from thermal_model import MakeRandomThermalModel
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
defaultThermal = 3


class PythonInterface:
    def XPluginStart(self):
        global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl
        
        global myMenu
        mySubMenuItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "Thermal Simulator", 0, 1)
        self.MyMenuHandlerCB = self.MyMenuHandlerCallback
        self.myMenu = XPLMCreateMenu(self, "Thermals", XPLMFindPluginsMenu(), mySubMenuItem, self.MyMenuHandlerCB,   0)
        XPLMAppendMenuItem(self.myMenu, "Toggle Thermal visibility", toggleThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Randomize Thermals", randomThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Default Thermals", defaultThermal, 1)

        
        world.thermals_visible = True
        
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
        world.world_update = True
        
        # variables to inject energy to the plane 
        self.lift = EasyDref('sim/flightmodel/forces/fnrml_plug_acf', 'float')
        self.roll = EasyDref('sim/flightmodel/forces/L_plug_acf', 'float') # wing roll     
        # although lift should be enough, some energy has to go as thrust, or the plane
        # might float in the air without moving!
        self.thrust  = EasyDref('sim/flightmodel/forces/faxil_plug_acf', 'float')

           

        #world.thermal_map = MakeThermalModelFromlist(world.default_thermal_list)
        world.thermal_map = MakeRandomThermalModel(80,300) # quantity,diameter
        # image to mark thermals
        self.ObjectPath = "lib/dynamic/balloon.obj" 
        self.ObjectPath1 = "lib/ships/Frigate.obj" 
        
        self.locations = DrawThermalMap() 

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

    def LoadObject1(self, fname, ref):
        self.Object1 = XPLMLoadObject(fname)        
     
    def DrawObject(self, inPhase, inIsBefore, inRefcon):
        if not world.thermals_visible :  # exit if visibility is off !
            return 1
    
        self.LoadObjectCB = self.LoadObject
        self.LoadObjectCB1 = self.LoadObject1
        XPLMLookupObjects(self, self.ObjectPath, 0, 0, self.LoadObjectCB, 0)  
        XPLMLookupObjects(self, self.ObjectPath1, 0, 0, self.LoadObjectCB1, 0)  
        
        # build object list for drawing
        if world.world_update :
           self.locations = DrawThermalMap()   #get the locations where to draw the objects..
           world.world_update = False
           print "number of draw objects = ", len(self.locations)
           
        #locations = self.locations
        #-----------
        locations1 = self.locations[:len(self.locations)/2]
        locations2 = self.locations[len(self.locations)/2:]
        #print "object1"
        XPLMDrawObjects(self.Object, len(locations1), locations1, 0, 1)
        #print "object2"
        XPLMDrawObjects(self.Object1, len(locations2), locations2, 0, 1)
        #print "done"
        #----------------
        #XPLMDrawObjects(self.Object, len(locations), locations, 0, 1)
        return 1

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        # instantiate the actual callbacks.  
        elapsed = XPLMGetElapsedTime()
        lat = XPLMGetDataf(self.PlaneLat)
        lon = XPLMGetDataf(self.PlaneLon)
        elevation = XPLMGetDataf(self.PlaneElev)
        heading = XPLMGetDataf(self.PlaneHdg)
        roll_angle = XPLMGetDataf(self.PlaneRol)
        wind_speed = round(XPLMGetDataf(self.WindSpeed)*0.5144, 2 )      # Knots to m/s
        wind_dir = round(math.radians( XPLMGetDataf(self.WindDir) ), 4 ) # Degrees to radians

        #keep up with wind changes
        if [wind_speed,wind_dir] <>  [world.wind_speed,world.wind_dir] :
            [world.wind_speed,world.wind_dir] = [wind_speed,wind_dir]  #insert wind vector into matrix 
            world.world_update = True
            print "wind changed",wind_speed,world.wind_speed,wind_dir,world.wind_dir
        
        #Get the lift value of the current position from the world thermal map
        lift_val, roll_val  = CalcThermal(lat,lon,elevation,heading,roll_angle)    
        
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
        #apply a roll to the plane 
        rval = roll_val * 3000 + self.roll.value #5000
        self.roll.value = rval
        
        # set the next callback time in +n for # of seconds and -n for # of Frames
        return .01 # works good on my (pretty fast) machine..

    def MyMenuHandlerCallback(self, inMenuRef, inItemRef):
            if (inItemRef == toggleThermal):
                world.thermals_visible = not world.thermals_visible
                print " Thermal Visibility  ", world.thermals_visible
            
            if (inItemRef == randomThermal):
                world.lat_origin = int(XPLMGetDataf(self.PlaneLat))
                world.lon_origin = int(XPLMGetDataf(self.PlaneLon))
                world.thermal_map = MakeRandomThermalModel(80,200)
                world.world_update = True
                print "Randomizing thermals"
                        

            if (inItemRef == defaultThermal):
                world.thermal_list = world.default_thermal_list
                world.thermal_map = MakeThermalModelFromList(world.thermal_list)
                world.world_update = True
                print "Making thermals from list"
                       
