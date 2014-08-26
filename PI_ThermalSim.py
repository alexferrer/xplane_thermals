"""
Thermal simulator  Ver .03  
  ** Works on Xplane 10.30 and above only **
  
  The plugin then reads the lift value of the plane current position and applies
  the lift & roll values. 
  
  Author: Alex Ferrer
  License: GPL 
"""

import world

from XPLMDefs import *
from EasyDref import EasyDref

#thermal modeling tools
from thermal_model import CalcThermal
from thermal_model import DrawThermal
from thermal_model import DrawThermalMap
from thermal_model import MakeRandomThermalMap


from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *

from random import randrange
import math

#for graphics
from XPLMDisplay import *
from XPLMGraphics import * 

#for yprobe
from XPLMScenery import *

#for menus
from XPLMMenus import *
from XPLMPlugin import *
from XPLMMenus import *
from XPWidgets import *
from XPWidgetDefs import *
from XPStandardWidgets import *
from XPLMPlugin import *

toggleThermal = 1
randomThermal = 2
defaultThermal = 3
aboutThermal = 4


class PythonInterface:
    def XPluginStart(self):
        global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl
        
        #----- menu stuff --------------------------
        #init menu control params       
        self.TCMenuItem = 0
        self.AboutMenuItem = 0        
        
        global myMenu
        mySubMenuItem = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "Thermal Simulator", 0, 1)
        self.MyMenuHandlerCB = self.MyMenuHandlerCallback
        self.myMenu = XPLMCreateMenu(self, "Thermals", XPLMFindPluginsMenu(), mySubMenuItem, self.MyMenuHandlerCB, 0)
        XPLMAppendMenuItem(self.myMenu, "Thermal Visibility On/Off " , toggleThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Configure Thermals", randomThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Load Thermals", defaultThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "About", aboutThermal, 1)
        #-------------------------------------------------
        
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

        #sun pitch from flat in OGL coordinates degrees, for thermal strength calculation
        # from zero to 90 at 12pm in summer near the equator .. 
        self.SunPitch  = XPLMFindDataRef('sim/graphics/scenery/sun_pitch_degrees')
        #temperature_sealevel_c
        #dewpoi_sealevel_c
        
        # terrain probe to test for height and water
        world.probe = XPLMCreateProbe(xplm_ProbeY)


        
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
        # instantiate the actual callbacks.  
        elapsed = XPLMGetElapsedTime()
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
        #lift_val = 1000
        #roll_val = 0
        '''------------------------------------------------------------------------'''

        #apply the force to the airplanes lift.value dataref
        lval = lift_val * world.lift_factor + self.lift.value  
        self.lift.value = lval  
        
        # although extra lift is what should be happening...
        # adding a bit of thrust works much better! -150 = 1m/s
        # apply a max thurst to a factor of 500fpm
        if lift_val > 500 :
           lift_val = 500

        tval = self.thrust.value
        self.thrust.value = world.thrust_factor * lift_val + tval    
        
        #apply a roll to the plane 
        rval = roll_val * world.roll_factor + self.roll.value #5000
        self.roll.value = rval
        
        #--------------------- for testing probes only-------
        self.probe = XPLMCreateProbe(xplm_ProbeY)
        self.SDK200TestsObjectProbe = XPLMCreateProbe(xplm_ProbeY) 
        #----------------------------------------------------
        
        
        
        # set the next callback time in +n for # of seconds and -n for # of Frames
        return .01 # works good on my (pretty fast) machine..


    #--------------------------------------------------------------------------------------------------





    #                        M E N U   S T U F F 






    #------------------------------------ menu stuff  from here on ----------------------------------    

    def MyMenuHandlerCallback(self, inMenuRef, inItemRef):
        if (inItemRef == toggleThermal):
            print " Thermal Visibility  "
            world.thermals_visible = not world.thermals_visible

            
        if (inItemRef == randomThermal):
            print "show thermal config box "
            if (self.TCMenuItem == 0):
                print " create the thermal config box "
                self.CreateTCWindow(100, 550, 550, 330)
                self.TCMenuItem = 1
            else:
                if(not XPIsWidgetVisible(self.TCWidget)):
                    print "re-show test config box "
                    XPShowWidget(self.TCWidget)

        if (inItemRef == defaultThermal):
            print "Making thermals from list"


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
                lat = XPLMGetDataf(self.PlaneLat)
                lon = XPLMGetDataf(self.PlaneLon)
                world.cloud_streets = XPGetWidgetProperty(self.enableCheck, xpProperty_ButtonState, None)
                                                       # lat,lon,stregth,count
                world.thermal_dict = MakeRandomThermalMap(lat,lon,world.thermal_power,world.thermal_density,world.thermal_size)    
                world.world_update = True
                return 1
                

            if (inParam1 == self.TRandom_button):
                print "Set thermal config randomly" 
                return 1

        
        if (inMessage == xpMsg_ScrollBarSliderPositionChanged):
            #Thermal Tops
            val = XPGetWidgetProperty(self.TTops_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TTops_value, str(val))
            world.thermal_tops = val * world.f2m
            
            #Thermal Density
            val = XPGetWidgetProperty(self.TDensity_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            XPSetWidgetDescriptor(self.TDensity_value, str(val))
            world.thermal_density = val
            
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

        return 0

    def AboutHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xpMessage_CloseButtonPushed):
            print "about close button pushed"
            if (self.AboutMenuItem == 1):
                print "hide the widget"
                XPHideWidget(self.AboutWidget)
                return 1
        return 0

        
    # Creates the widget with buttons for test and edit boxes for info
    def CreateTCWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "Thermal generator Configuration" 
        
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

        # Thermal Density
        self.TDensity_label1 = XPCreateWidget(x+60,  y-80, x+140, y-102,1,"Thermal Density", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDensity_label2 = XPCreateWidget(x+375, y-80, x+410, y-102,1,"# of Thermals", 0, self.TCWidget, xpWidgetClass_Caption)
        #define scrollbar
        self.TDensity_value = XPCreateWidget(x+260, y-68, x+330, y-82,1,"  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDensity_scrollbar = XPCreateWidget(x+170, y-80, x+370, y-102, 1, "", 0,self.TCWidget,xpWidgetClass_ScrollBar)
        XPSetWidgetProperty(self.TDensity_scrollbar, xpProperty_ScrollBarMin, 10);
        XPSetWidgetProperty(self.TDensity_scrollbar, xpProperty_ScrollBarMax, 100);
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
        XPSetWidgetProperty(self.TPower_scrollbar, xpProperty_ScrollBarMax, 2500);
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

        #Define checkbox for cloud streets
        XPCreateWidget(x+60, y-80, x+140, y-102, 1, 'Align on cloud streets', 0,self.TCWidget, xpWidgetClass_Caption)
        self.enableCheck = XPCreateWidget(x+180, y-80, x+220, y-102, 1, '', 0,self.TCWidget, xpWidgetClass_Button)
        XPSetWidgetProperty(self.enableCheck, xpProperty_ButtonType, xpRadioButton)
        XPSetWidgetProperty(self.enableCheck, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        XPSetWidgetProperty(self.enableCheck, xpProperty_ButtonState, world.cloud_streets)
        y -=75

        #define button 
        self.TRandom_button = XPCreateWidget(x+60, y-60, x+200, y-82,
                                           1, "Surprise me!", 0,self.TCWidget,xpWidgetClass_Button)
        XPSetWidgetProperty(self.TRandom_button, xpProperty_ButtonType, xpPushButton)

        #define button 
        self.TGenerate_button = XPCreateWidget(x+320, y-60, x+440, y-82,
                                           1, "Generate Thermals", 0,self.TCWidget,xpWidgetClass_Button)
        XPSetWidgetProperty(self.TGenerate_button, xpProperty_ButtonType, xpPushButton)
        
        
        # --------------------------
        self.TCHandlerCB = self.TCHandler
        XPAddWidgetCallback(self,self.TCWidget, self.TCHandlerCB)

    # Creates the widget with buttons for test and edit boxes for info
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
        

        # --------------------------
        self.AboutHandlerCB = self.AboutHandler
        XPAddWidgetCallback(self,self.AboutWidget, self.AboutHandlerCB)






