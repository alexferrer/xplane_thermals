"""
Thermal simulator  Ver .04  
  ** Works on Xplane 10.30 and above only **
  
  The plugin then reads the lift value of the plane current position and
  sets the lift & roll values. 
  
  Author: Alex Ferrer
  License: GPL 
"""

import world

from XPLMDefs import *
from EasyDref import EasyDref

# thermal modeling tools
from thermal_model import CalcThermal
from thermal_model import DrawThermal
from thermal_model import DrawThermalMap
from thermal_model import MakeRandomThermalMap
from thermal_model import MakeCSVThermalMap

from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *

import random
from random import randrange, seed
import math

# for graphics
from XPLMDisplay import *
from XPLMGraphics import * 

# for yprobe
from XPLMScenery import *

# for menus
from XPLMMenus import *
from XPLMPlugin import *
from XPLMMenus import *
from XPWidgets import *
from XPWidgetDefs import *
from XPStandardWidgets import *
from XPLMPlugin import *

toggleThermal = 1
randomThermal = 2
csvThermal = 3
aboutThermal = 4
configGlider = 5

# add random seed for multiplayer session - just press "reset seed" and then 
# "generate thermals"
seed_number = world.seed_number

def xplane_world_to_local(lat, lon, alt):
    x,y,z = XPLMWorldToLocal(lat,lon,alt)
    return (x,y,z)


def xplane_terrain_is_water(lat, lon):
    info = []       
    x,y,z = XPLMWorldToLocal(lat,lon,0)
    if XPLMProbeTerrainXYZ(world.probe,x,y,z,info) == xplm_ProbeHitTerrain:
        if info[10]:
            return True
    return False


class PythonInterface:
    def XPluginStart(self):
        global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl
        
        # ----- menu stuff --------------------------
        # init menu control params       
        self.TCMenuItem = 0
        self.CSVMenuItem = 0
        self.CGMenuItem = 0
        self.AboutMenuItem = 0       
         
        
        global myMenu
        mySubMenuItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "Thermal Simulator", 0, 1)
        self.MyMenuHandlerCB = self.MyMenuHandlerCallback
        self.myMenu = XPLMCreateMenu(self, "Thermals", XPLMFindPluginsMenu(), mySubMenuItem, self.MyMenuHandlerCB, 0)
        XPLMAppendMenuItem(self.myMenu, "Thermal Visibility On/Off " , toggleThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Generate Random Thermals", randomThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Generate CSV Thermals", csvThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Configure Glider", configGlider, 1)
        XPLMAppendMenuItem(self.myMenu, "About", aboutThermal, 1)
        # -------------------------------------------------
        
        world.thermals_visible = False
        
        self.Name = "ThermalSim2"
        self.Sig =  "AlexFerrer.Python.ThermalSim2"
        self.Desc = "A plugin that simulates thermals (beta)"

        """ Data refs we want to record."""
        # airplane current flight info
        self.PlaneLat  = XPLMFindDataRef("sim/flightmodel/position/latitude")
        self.PlaneLon  = XPLMFindDataRef("sim/flightmodel/position/longitude")
        self.PlaneElev = XPLMFindDataRef("sim/flightmodel/position/elevation")
        self.PlaneHdg  = XPLMFindDataRef("sim/flightmodel/position/psi") # plane heading
        self.PlaneRol  = XPLMFindDataRef("sim/flightmodel/position/phi") # plane roll
        
        self.WindSpeed = XPLMFindDataRef("sim/weather/wind_speed_kt[0]") # wind speed at surface
        self.WindDir   = XPLMFindDataRef("sim/weather/wind_direction_degt[0]") # wind direction
        
        # is the sim paused?
        self.runningTime  = XPLMFindDataRef("sim/time/total_running_time_sec")
        self.sim_time = 0 
        
        # sun pitch from flat in OGL coordinates degrees, for thermal strength calculation
        # from zero to 90 at 12pm in summer near the equator .. 
        self.SunPitch  = XPLMFindDataRef('sim/graphics/scenery/sun_pitch_degrees')
        # temperature_sealevel_c
        # dewpoi_sealevel_c
        
        # terrain probe to test for height and water
        world.probe = XPLMCreateProbe(xplm_ProbeY)
        world.world_to_local = xplane_world_to_local
        world.terrain_is_water = xplane_terrain_is_water
 
        # variables to inject energy to the plane 
        self.lift = EasyDref('sim/flightmodel/forces/fnrml_plug_acf', 'float')
        self.roll = EasyDref('sim/flightmodel/forces/L_plug_acf', 'float') # wing roll     
        # although lift should be enough, some energy has to go as thrust, or the plane
        # might float in the air without moving!
        self.thrust  = EasyDref('sim/flightmodel/forces/faxil_plug_acf', 'float')
        
        #Drawing update flag
        world.world_update = True
         
        # image to mark thermals
        self.ObjectPath = "lib/dynamic/balloon.obj"    

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
        XPLMDestroyMenu(self, self.myMenu)
        # for probe suff
        XPLMDestroyProbe(world.probe)

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
        if not world.thermals_visible :  # exit if visibility is off !
            return 1
    
        self.LoadObjectCB = self.LoadObject
        XPLMLookupObjects(self, self.ObjectPath, 0, 0, self.LoadObjectCB, 0)  
        
        # build object list for drawing
        if world.world_update :
           lat = XPLMGetDataf(self.PlaneLat)
           lon = XPLMGetDataf(self.PlaneLon)
           self.locations = DrawThermalMap(lat,lon)   #get the locations where to draw the objects..
           world.world_update = False
           #print "number of draw objects = ", len(self.locations)
           
        locations = self.locations
        if locations : # only draw if not zero !
            XPLMDrawObjects(self.Object, len(locations), locations, 0, 1)
        return 1

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
    
        # is the sim paused? , then skip
        runtime = XPLMGetDataf(self.runningTime)
        if self.sim_time == runtime :
           print "Paused!"
           return 1 
        self.sim_time = runtime
        
        # instantiate the actual callbacks.  
        
        lat = XPLMGetDataf(self.PlaneLat)
        lon = XPLMGetDataf(self.PlaneLon)
        elevation = XPLMGetDataf(self.PlaneElev)
        heading = XPLMGetDataf(self.PlaneHdg)
        roll_angle = XPLMGetDataf(self.PlaneRol)
        wind_speed = round(XPLMGetDataf(self.WindSpeed)*0.5144, 2 )      # Knots to m/s
        wind_dir = round(math.radians( XPLMGetDataf(self.WindDir) ), 4 ) # Degrees to radians
        
        #sun pitch afects thermal power , noon in summer is the best..
        sun_pitch = XPLMGetDataf(self.SunPitch) #Degrees
        sun_factor = (sun_pitch + 10)/100
        if sun_pitch < 0 :
           sun_factor = 0 

        #keep up with wind changes
        if [wind_speed,wind_dir] <>  [world.wind_speed,world.wind_dir] :
            [world.wind_speed,world.wind_dir] = [wind_speed,wind_dir]  
            world.world_update = True
            #print "wind changed",wind_speed,world.wind_speed,wind_dir,world.wind_dir
        
        #Get the lift value of the current position from the world thermal map
        lift_val, roll_val  = CalcThermal(lat,lon,elevation,heading,roll_angle)    
        
        # apply sun elevation as a % factor to thermal power 
        # average lift depends on sun angle over the earth. 
        lift_val = lift_val * sun_factor
        
        '''----------------------------- for fine tuning!!! -----------------------'''
        # lift_val = 500
        # roll_val = 0
        '''------------------------------------------------------------------------'''

        # apply the force to the airplanes lift.value dataref
        lval = lift_val * world.lift_factor + self.lift.value  
        self.lift.value = lval  
        
        # although extra lift is what should be happening...
        # adding a bit of thrust works much better! -150 = 1m/s
        # apply a max thurst to a factor of 500fpm
        if lift_val > 500 :
           lift_val = 500

        tval = self.thrust.value
        self.thrust.value = (- world.thrust_factor) * lift_val + tval    
        
        # apply a roll to the plane 
        rval = roll_val * world.roll_factor + self.roll.value 
        self.roll.value = rval
        
        # Terrain probe -------
        self.probe = XPLMCreateProbe(xplm_ProbeY)
        
        
        # set the next callback time in +n for # of seconds and -n for # of Frames
        return .01 # works good on my (pretty fast) machine..


    #--------------------------------------------------------------------------------------------------



    #                        M E N U   S T U F F 


    # ------------------------------------ menu stuff  from here on ----------------------------------    

    def MyMenuHandlerCallback(self, inMenuRef, inItemRef):
        if (inItemRef == toggleThermal):
            print " Thermal Visibility  "
            world.thermals_visible = not world.thermals_visible
            
        if (inItemRef == randomThermal):
            print "show thermal config box "
            if (self.TCMenuItem == 0):
                print " create the thermal config box "
                self.CreateTCWindow(100, 600, 600, 400)
                self.TCMenuItem = 1
            else:
                if(not XPIsWidgetVisible(self.TCWidget)):
                    print "re-show test config box "
                    XPShowWidget(self.TCWidget)

        if (inItemRef == csvThermal):
            print "Making thermals from list"
            if (self.CSVMenuItem == 0):
                print " create the thermal config box "
                self.CreateCSVWindow(100, 550, 550, 330)
                self.CSVMenuItem = 1
            else:
                if(not XPIsWidgetVisible(self.CSVWidget)):
                    print "re-show test config box "
                    XPShowWidget(self.CSVWidget)

        if (inItemRef == configGlider):
            print "show thermal config box "
            if (self.CGMenuItem == 0):
                print " create the thermal config box "
                self.CreateCGWindow(100, 550, 550, 330)
                self.CGMenuItem = 1
            else:
                if(not XPIsWidgetVisible(self.CGWidget)):
                    print "re-show test config box "
                    XPShowWidget(self.CGWidget)
                    
        print "------>",inItemRef
        if (inItemRef == aboutThermal):
            print "show about box "
            if (self.AboutMenuItem == 0):
                print " create the thermal config box "
                self.CreateAboutWindow(100, 550, 450, 230)
                self.AboutMenuItem = 1
            else:
                if(not XPIsWidgetVisible(self.AboutWidget)):
                    print "re-show about box "
                    XPShowWidget(self.AboutWidget)


    def TCHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xpMessage_CloseButtonPushed):
            print "close button pushed"
            if (self.TCMenuItem == 1):
                print "hide the widget"
                XPHideWidget(self.TCWidget)
                return 1
                
        # Process when a button on the widget is pressed
        if (inMessage == xpMsg_PushButtonPressed):
            print "[button was pressed",inParam1,"]"

            # Tests the Command API, will find command
            if (inParam1 == self.TGenerate_button):
                print "Generate" 
                print world.seed_number
                print "minimum separation between thermals "
                print world.thermal_distance
                random.seed(world.seed_number)
                lat = XPLMGetDataf(self.PlaneLat)
                lon = XPLMGetDataf(self.PlaneLon)
                # world.cloud_streets = XPGetWidgetProperty(self.enableCheck, xpProperty_ButtonState, None)
                                                       # lat,lon,stregth,count
                world.thermal_dict = MakeRandomThermalMap(lat,lon,world.thermal_power,world.thermal_density,world.thermal_size)    
                world.world_update = True
                return 1
                

        
        if (inMessage == xpMsg_ScrollBarSliderPositionChanged):
            #Thermal Tops
            val = XPGetWidgetProperty(self.TTops_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TTops_value, str(val))
            world.thermal_tops = int( val * world.f2m )
            
            #Thermal Density
            val = XPGetWidgetProperty(self.TDensity_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TDensity_value, str(val))
            world.thermal_density = val
            
            #Minimum Distance Between  Thermals
            val = XPGetWidgetProperty(self.TDistance_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TDistance_value, str(val))
            world.thermal_distance =  val 
            
            #Thermal Size
            val = XPGetWidgetProperty(self.TSize_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TSize_value, str(val))
            world.thermal_size = val
            
            #Thermal Power
            val = XPGetWidgetProperty(self.TPower_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TPower_value, str(val))
            world.thermal_power = val
            
            #Thermal Cycle
            val = XPGetWidgetProperty(self.TCycle_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TCycle_value, str(val))
            world.thermal_cycle = val

            #Seed
            val = XPGetWidgetProperty(self.TSeed_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TSeed_value, str(val))
            world.seed_number = val

        return 0


        
    # Creates the widget with buttons for test and edit boxes for info
    def CreateTCWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "Thermal Generator Configuration" 
        
        #create the window
        self.TCWidget = XPCreateWidget(x, y, x2, y2, 1, Title, 1,     0, xpWidgetClass_MainWindow)        
        XPSetWidgetProperty(self.TCWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        TCWindow = XPCreateWidget(x+50, y-50, x2-50, y2+50, 1, "",     0,self.TCWidget, xpWidgetClass_SubWindow)
        XPSetWidgetProperty(TCWindow, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

        #-----------------------------
        # Thermal Tops
        self.TTops_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermals Tops", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TTops_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Feet", 0, self.TCWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.TTops_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TTops_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.TCWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.TTops_scrollbar, xpProperty_ScrollBarMin, 100);
        XPSetWidgetProperty(self.TTops_scrollbar, xpProperty_ScrollBarMax, 20000);
        XPSetWidgetProperty(self.TTops_scrollbar, xpProperty_ScrollBarPageAmount,500)        
        XPSetWidgetProperty(self.TTops_scrollbar, xpProperty_ScrollBarSliderPosition, int(world.thermal_tops*world.m2f) )               
        XPSetWidgetDescriptor(self.TTops_value, str( int(world.thermal_tops*world.m2f) ))
        y -=32

        # Thermal Distance
        self.TDistance_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermals Separation", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDistance_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Meters", 0, self.TCWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.TDistance_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDistance_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.TCWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.TDistance_scrollbar, xpProperty_ScrollBarMin, 100);
        XPSetWidgetProperty(self.TDistance_scrollbar, xpProperty_ScrollBarMax, 5000);
        XPSetWidgetProperty(self.TDistance_scrollbar, xpProperty_ScrollBarPageAmount,100)        
        XPSetWidgetProperty(self.TDistance_scrollbar, xpProperty_ScrollBarSliderPosition, int(world.thermal_distance) )               
        XPSetWidgetDescriptor(self.TDistance_value, str( int(world.thermal_distance) ))
        y -=32

        # Thermal Density
        self.TDensity_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermal Density", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDensity_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"# of Thermals", 0, self.TCWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.TDensity_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDensity_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.TCWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.TDensity_scrollbar, xpProperty_ScrollBarMin, 10);
        XPSetWidgetProperty(self.TDensity_scrollbar, xpProperty_ScrollBarMax, 500);
        XPSetWidgetProperty(self.TDensity_scrollbar, xpProperty_ScrollBarPageAmount,10)
        XPSetWidgetProperty(self.TDensity_scrollbar, xpProperty_ScrollBarSliderPosition,world.thermal_density)               
        XPSetWidgetDescriptor(self.TDensity_value, str(world.thermal_density))
        y -=32

        # Thermal Size
        self.TSize_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermal Size", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TSize_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Max Diameter m", 0, self.TCWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.TSize_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TSize_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.TCWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.TSize_scrollbar, xpProperty_ScrollBarMin, 50);
        XPSetWidgetProperty(self.TSize_scrollbar, xpProperty_ScrollBarMax, 1500);
        XPSetWidgetProperty(self.TSize_scrollbar, xpProperty_ScrollBarPageAmount,20)
        XPSetWidgetProperty(self.TSize_scrollbar, xpProperty_ScrollBarSliderPosition,world.thermal_size)
        XPSetWidgetDescriptor(self.TSize_value, str(world.thermal_size))
        y -=32

        # Thermal Strength
        self.TPower_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermal Power", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TPower_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Max fpm", 0, self.TCWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.TPower_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TPower_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.TCWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.TPower_scrollbar, xpProperty_ScrollBarMin, 250);
        XPSetWidgetProperty(self.TPower_scrollbar, xpProperty_ScrollBarMax, 3500);
        XPSetWidgetProperty(self.TPower_scrollbar, xpProperty_ScrollBarPageAmount,10)
        XPSetWidgetProperty(self.TPower_scrollbar, xpProperty_ScrollBarSliderPosition,world.thermal_power)
        XPSetWidgetDescriptor(self.TPower_value, str(world.thermal_power))
        y -=32

        # Thermal Cycle time
        self.TCycle_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Cycle Time", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TCycle_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Minutes", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TCycle_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TCycle_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.TCWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.TCycle_scrollbar, xpProperty_ScrollBarMin, 5);
        XPSetWidgetProperty(self.TCycle_scrollbar, xpProperty_ScrollBarMax, 90);
        XPSetWidgetProperty(self.TCycle_scrollbar, xpProperty_ScrollBarPageAmount,1)
        XPSetWidgetProperty(self.TCycle_scrollbar, xpProperty_ScrollBarSliderPosition,world.thermal_cycle)               
        XPSetWidgetDescriptor(self.TCycle_value, str(world.thermal_cycle))
        y -=30

        # Seed
        self.TSeed_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Seed Number", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TSeed_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TSeed_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.TCWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.TSeed_scrollbar, xpProperty_ScrollBarMin, 1234);
        XPSetWidgetProperty(self.TSeed_scrollbar, xpProperty_ScrollBarMax, 1334);
        XPSetWidgetProperty(self.TSeed_scrollbar, xpProperty_ScrollBarPageAmount,1)
        XPSetWidgetProperty(self.TSeed_scrollbar, xpProperty_ScrollBarSliderPosition,world.seed_number)               
        XPSetWidgetDescriptor(self.TSeed_value, str(world.seed_number))
        y -=75

        #Define checkbox for cloud streets
        #XPCreateWidget(x+60, y-80, x+140, y-102, 1, 'Align on cloud streets', 0,self.TCWidget, xpWidgetClass_Caption)
        #self.enableCheck = XPCreateWidget(x+180, y-80, x+220, y-102, 1, '', 0,self.TCWidget, xpWidgetClass_Button)
        #XPSetWidgetProperty(self.enableCheck, xpProperty_ButtonType, xpRadioButton)
        #XPSetWidgetProperty(self.enableCheck, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        #XPSetWidgetProperty(self.enableCheck, xpProperty_ButtonState, world.cloud_streets)
        #y -=75

        #define button 
        self.TGenerate_button = XPCreateWidget(x+320, y-60, x+440, y-82,
                                           1, "Generate Thermals", 0,self.TCWidget,xpWidgetClass_Button)
        XPSetWidgetProperty(self.TGenerate_button, xpProperty_ButtonType, xpPushButton)
        
        
        # --------------------------
        self.TCHandlerCB = self.TCHandler
        XPAddWidgetCallback(self,self.TCWidget, self.TCHandlerCB)




#----------------------- About Window
    def CreateAboutWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "About Thermal Simulator" 
        
        #create the window
        self.AboutWidget = XPCreateWidget(x, y, x2, y2, 1, Title, 1,     0, xpWidgetClass_MainWindow)        
        XPSetWidgetProperty(self.AboutWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        AboutWindow = XPCreateWidget(x+50, y-50, x2-50, y2+50, 1, "",     0,self.AboutWidget, xpWidgetClass_SubWindow)
        XPSetWidgetProperty(AboutWindow, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

        text1 = "Thermal Simulator"
        self.About_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1, text1, 0, self.AboutWidget, xpWidgetClass_Caption)
        y -=35

        text2 = "Author: Alex Ferrer  @ 2014"
        self.About_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1, text2, 0, self.AboutWidget, xpWidgetClass_Caption)
        y -=35

        text3 = " https://github.com/alexferrer/xplane_thermals/wiki"
        self.About_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1, text3, 0, self.AboutWidget, xpWidgetClass_Caption)

        self.AboutHandlerCB = self.AboutHandler
        XPAddWidgetCallback(self,self.AboutWidget, self.AboutHandlerCB)
     # ----
     
    def AboutHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xpMessage_CloseButtonPushed):
            print "about close button pushed"
            if (self.AboutMenuItem == 1):
                print "hide the widget"
                XPHideWidget(self.AboutWidget)
                return 1
        return 0
#----------------------------------------- new...

    def CGHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xpMessage_CloseButtonPushed):
            print "close button pushed"
            if (self.CGMenuItem == 1):
                print "hide the widget"
                XPHideWidget(self.CGWidget)
                return 1
                
        # Process when a button on the widget is pressed
        if (inMessage == xpMsg_PushButtonPressed):
            print "[button was pressed",inParam1,"]"

            # Tests the Command API, will find command
            if (inParam1 == self.CGGenerate_button):
                print "Generate" 
                return 1
                

            if (inParam1 == self.CGRandom_button):
                print "Set thermal config randomly" 
                return 1

        
        if (inMessage == xpMsg_ScrollBarSliderPositionChanged):
            #Lift Factor
            val = XPGetWidgetProperty(self.CGLift_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CGLift_value, str(val))
            world.lift_factor = val * .1
            
            #Thrust Factor
            val = XPGetWidgetProperty(self.CGThrust_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CGThrust_value, str(val))
            world.thrust_factor = val * .1
            
            #Roll factor
            val = XPGetWidgetProperty(self.CGRoll_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CGRoll_value, str(val))
            world.roll_factor = val *.1
            
            #Wing Size
            val = XPGetWidgetProperty(self.CGWing_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CGWing_value, str(val))
            world.wing_size = val

        return 0


        
    # Creates the config glider widget
    def CreateCGWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "Glider Energy Configuration" 
        
        #create the window
        self.CGWidget = XPCreateWidget(x, y, x2, y2, 1, Title, 1,     0, xpWidgetClass_MainWindow)        
        XPSetWidgetProperty(self.CGWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        CGWindow = XPCreateWidget(x+50, y-50, x2-50, y2+50, 1, "",     0,self.CGWidget, xpWidgetClass_SubWindow)
        XPSetWidgetProperty(CGWindow, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

        #-----------------------------
        # Lift Component
        self.CGLift_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Lift Factor", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGLift_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Units", 0, self.CGWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.CGLift_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGLift_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CGWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CGLift_scrollbar, xpProperty_ScrollBarMin, 0);
        XPSetWidgetProperty(self.CGLift_scrollbar, xpProperty_ScrollBarMax, 100);
        XPSetWidgetProperty(self.CGLift_scrollbar, xpProperty_ScrollBarPageAmount,1)        
        XPSetWidgetProperty(self.CGLift_scrollbar, xpProperty_ScrollBarSliderPosition, int(world.lift_factor*10) )               
        XPSetWidgetDescriptor(self.CGLift_value, str( int(world.lift_factor*10) ))
        y -=32

        # Thrust Component
        self.CGThrust_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thrust Factor", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGThrust_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Units", 0, self.CGWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.CGThrust_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGThrust_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CGWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CGThrust_scrollbar, xpProperty_ScrollBarMin, 0);
        XPSetWidgetProperty(self.CGThrust_scrollbar, xpProperty_ScrollBarMax, 100);
        XPSetWidgetProperty(self.CGThrust_scrollbar, xpProperty_ScrollBarPageAmount,1)
        XPSetWidgetProperty(self.CGThrust_scrollbar, xpProperty_ScrollBarSliderPosition,world.thrust_factor*10)               
        XPSetWidgetDescriptor(self.CGThrust_value, str(world.thrust_factor*10))
        y -=32

        # Roll Component
        self.CGRoll_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Roll Factor", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGRoll_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Units", 0, self.CGWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.CGRoll_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGRoll_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CGWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CGRoll_scrollbar, xpProperty_ScrollBarMin, 0);
        XPSetWidgetProperty(self.CGRoll_scrollbar, xpProperty_ScrollBarMax, 800);
        XPSetWidgetProperty(self.CGRoll_scrollbar, xpProperty_ScrollBarPageAmount,10)
        XPSetWidgetProperty(self.CGRoll_scrollbar, xpProperty_ScrollBarSliderPosition,world.roll_factor)
        XPSetWidgetDescriptor(self.CGRoll_value, str(world.roll_factor))
        y -=32

        # Wing Size
        self.CGWing_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Wing Size", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGWing_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"meters", 0, self.CGWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.CGWing_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGWing_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CGWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CGWing_scrollbar, xpProperty_ScrollBarMin, 1);
        XPSetWidgetProperty(self.CGWing_scrollbar, xpProperty_ScrollBarMax, 30);
        XPSetWidgetProperty(self.CGWing_scrollbar, xpProperty_ScrollBarPageAmount,1)
        XPSetWidgetProperty(self.CGWing_scrollbar, xpProperty_ScrollBarSliderPosition,world.wing_size)
        XPSetWidgetDescriptor(self.CGWing_value, str(world.wing_size))
        y -=32


        #Define checkbox for cloud streets
        XPCreateWidget(x+60, y-80, x+140, y-102, 1, 'xx3', 0,self.CGWidget, xpWidgetClass_Caption)
        self.enableCheck1 = XPCreateWidget(x+180, y-80, x+220, y-102, 1, '', 0,self.CGWidget, xpWidgetClass_Button)
        XPSetWidgetProperty(self.enableCheck1, xpProperty_ButtonType, xpRadioButton)
        XPSetWidgetProperty(self.enableCheck1, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        XPSetWidgetProperty(self.enableCheck1, xpProperty_ButtonState, world.cloud_streets)
        y -=75

        #define button 
        self.CGRandom_button = XPCreateWidget(x+60, y-60, x+200, y-82,
                                           1, "xx2", 0,self.CGWidget,xpWidgetClass_Button)
        XPSetWidgetProperty(self.CGRandom_button, xpProperty_ButtonType, xpPushButton)

        #define button 
        self.CGGenerate_button = XPCreateWidget(x+320, y-60, x+440, y-82,
                                           1, "xxx1", 0,self.CGWidget,xpWidgetClass_Button)
        XPSetWidgetProperty(self.CGGenerate_button, xpProperty_ButtonType, xpPushButton)
        
        
        # --------------------------
        self.CGHandlerCB = self.CGHandler
        XPAddWidgetCallback(self,self.CGWidget, self.CGHandlerCB)

        # CSV MENU

    def CSVHandler(self, inMessage, inWidget, inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xpMessage_CloseButtonPushed):
            print "close button pushed"
            if (self.CSVMenuItem == 1):
                print "hide the widget"
                XPHideWidget(self.CSVWidget)
                return 1
                
        # Process when a button on the widget is pressed
        if (inMessage == xpMsg_PushButtonPressed):
            print "[button was pressed",inParam1,"]"

            # Tests the Command API, will find command
            if (inParam1 == self.CSVTGenerate_button):
                print "Generate" 
                print world.seed_number
                random.seed(world.seed_number)
                lat = XPLMGetDataf(self.PlaneLat)
                lon = XPLMGetDataf(self.PlaneLon)
                world.thermal_dict = MakeCSVThermalMap(lat,lon,world.thermal_power,world.thermal_density,world.thermal_size)    
                world.world_update = True
                return 1
                

        
        if (inMessage == xpMsg_ScrollBarSliderPositionChanged):
            #Thermal Tops
            val = XPGetWidgetProperty(self.CSVTTops_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CSVTTops_value, str(val))
            world.thermal_tops = int( val * world.f2m )
            
            #Thermal Density
            val = XPGetWidgetProperty(self.CSVTDensity_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CSVTDensity_value, str(val))
            world.thermal_density = val
            
            #Thermal Size
            val = XPGetWidgetProperty(self.CSVTSize_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CSVTSize_value, str(val))
            world.thermal_size = val
            
            #Thermal Power
            val = XPGetWidgetProperty(self.CSVTPower_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CSVTPower_value, str(val))
            world.thermal_power = val
            
            #Thermal Cycle
            val = XPGetWidgetProperty(self.CSVTCycle_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CSVTCycle_value, str(val))
            world.thermal_cycle = val

            #Seed
            val = XPGetWidgetProperty(self.CSVSeed_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.CSVSeed_value, str(val))
            world.seed_number = val

        return 0


        
    # Creates the widget with buttons for test and edit boxes for info
    def CreateCSVWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "Thermal generation from CSV" 
        
        #create the window
        self.CSVWidget = XPCreateWidget(x, y, x2, y2, 1, Title, 1,     0, xpWidgetClass_MainWindow)        
        XPSetWidgetProperty(self.CSVWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        CSVWindow = XPCreateWidget(x+50, y-50, x2-50, y2+50, 1, "",     0,self.CSVWidget, xpWidgetClass_SubWindow)
        XPSetWidgetProperty(CSVWindow, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

        #-----------------------------
        # Thermal Tops
        self.CSVTTops_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermals Tops", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTTops_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Feet", 0, self.CSVWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.CSVTTops_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTTops_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CSVWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CSVTTops_scrollbar, xpProperty_ScrollBarMin, 100);
        XPSetWidgetProperty(self.CSVTTops_scrollbar, xpProperty_ScrollBarMax, 20000);
        XPSetWidgetProperty(self.CSVTTops_scrollbar, xpProperty_ScrollBarPageAmount,500)        
        XPSetWidgetProperty(self.CSVTTops_scrollbar, xpProperty_ScrollBarSliderPosition, int(world.thermal_tops*world.m2f) )               
        XPSetWidgetDescriptor(self.CSVTTops_value, str( int(world.thermal_tops*world.m2f) ))
        y -=32

        # Thermal Density
        self.CSVTDensity_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermal Density", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTDensity_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Max # of Thermals", 0, self.CSVWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.CSVTDensity_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTDensity_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CSVWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CSVTDensity_scrollbar, xpProperty_ScrollBarMin, 1);
        XPSetWidgetProperty(self.CSVTDensity_scrollbar, xpProperty_ScrollBarMax, 500);
        XPSetWidgetProperty(self.CSVTDensity_scrollbar, xpProperty_ScrollBarPageAmount,10)
        XPSetWidgetProperty(self.CSVTDensity_scrollbar, xpProperty_ScrollBarSliderPosition,world.thermal_density)               
        XPSetWidgetDescriptor(self.CSVTDensity_value, str(world.thermal_density))
        y -=32

        # Thermal Size
        self.CSVTSize_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermal Size", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTSize_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Max Diameter m", 0, self.CSVWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.CSVTSize_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTSize_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CSVWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CSVTSize_scrollbar, xpProperty_ScrollBarMin, 50);
        XPSetWidgetProperty(self.CSVTSize_scrollbar, xpProperty_ScrollBarMax, 1500);
        XPSetWidgetProperty(self.CSVTSize_scrollbar, xpProperty_ScrollBarPageAmount,20)
        XPSetWidgetProperty(self.CSVTSize_scrollbar, xpProperty_ScrollBarSliderPosition,world.thermal_size)
        XPSetWidgetDescriptor(self.CSVTSize_value, str(world.thermal_size))
        y -=32

        # Thermal Strength
        self.CSVTPower_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermal Power", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTPower_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Max fpm", 0, self.CSVWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.CSVTPower_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTPower_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CSVWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CSVTPower_scrollbar, xpProperty_ScrollBarMin, 250);
        XPSetWidgetProperty(self.CSVTPower_scrollbar, xpProperty_ScrollBarMax, 3500);
        XPSetWidgetProperty(self.CSVTPower_scrollbar, xpProperty_ScrollBarPageAmount,10)
        XPSetWidgetProperty(self.CSVTPower_scrollbar, xpProperty_ScrollBarSliderPosition,world.thermal_power)
        XPSetWidgetDescriptor(self.CSVTPower_value, str(world.thermal_power))
        y -=32

        # Thermal Cycle time
        self.CSVTCycle_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Cycle Time", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTCycle_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"Minutes", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTCycle_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTCycle_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CSVWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CSVTCycle_scrollbar, xpProperty_ScrollBarMin, 5);
        XPSetWidgetProperty(self.CSVTCycle_scrollbar, xpProperty_ScrollBarMax, 90);
        XPSetWidgetProperty(self.CSVTCycle_scrollbar, xpProperty_ScrollBarPageAmount,1)
        XPSetWidgetProperty(self.CSVTCycle_scrollbar, xpProperty_ScrollBarSliderPosition,world.thermal_cycle)               
        XPSetWidgetDescriptor(self.CSVTCycle_value, str(world.thermal_cycle))
        y -=30

        # Seed
        self.CSVSeed_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Seed Number", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVSeed_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVSeed_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.CSVWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.CSVSeed_scrollbar, xpProperty_ScrollBarMin, 1234);
        XPSetWidgetProperty(self.CSVSeed_scrollbar, xpProperty_ScrollBarMax, 1334);
        XPSetWidgetProperty(self.CSVSeed_scrollbar, xpProperty_ScrollBarPageAmount,1)
        XPSetWidgetProperty(self.CSVSeed_scrollbar, xpProperty_ScrollBarSliderPosition,world.seed_number)               
        XPSetWidgetDescriptor(self.CSVSeed_value, str(world.seed_number))
        y -=75

        #define button 
        self.CSVTGenerate_button = XPCreateWidget(x+320, y-60, x+440, y-82,
                                           1, "Generate Thermals", 0,self.CSVWidget,xpWidgetClass_Button)
        XPSetWidgetProperty(self.CSVTGenerate_button, xpProperty_ButtonType, xpPushButton)
        
        
        # --------------------------
        self.CSVHandlerCB = self.CSVHandler
        XPAddWidgetCallback(self,self.CSVWidget, self.CSVHandlerCB)
