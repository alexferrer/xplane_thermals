"""
Thermal simulator  Ver .04
  ** Works on Xplane 12.x and above only **
  The plugin then reads the lift value of the plane current position and
  sets the lift & roll values.
  Author: Alex Ferrer
  License: GPL
"""

import world
# thermal modeling tools
from thermal_model import calc_thermalx, make_thermal_map_kk7
from thermal_model import make_random_thermal_map

from draw_thermals import drawThermalsOnScreen, eraseThermalsCloudsOnScreen, eraseThermalsRingsOnScreen, load_image_objects

import random
from random import randrange
import math

import xp
from XPPython3.xp_typing import *

#########################################################

# ------------------  T H E R M A L   S I M U L A T O R  ----------------------------
LIB_VERSION = "Version ----------------------------   PI_ThermalSim V2.0"
print(LIB_VERSION)

activatePlugin = 0
toggleThermal = 1
randomThermal = 2
csvThermal = 3
aboutThermal = 4
configGlider = 5
statsWindow = 6

def xplane_terrain_is_water(lat, lon):
    # https://xppython3.readthedocs.io/en/stable/development/changesfromp2.html?highlight=xplmprobeterrainxyz
    #info = []
    x, y, z = xp.worldToLocal(lat, lon, 0)
    info = xp.probeTerrainXYZ(world.probe, x, y, z)
    #print("xplmWorlprobe info = ",dir(info))

    if info.is_wet:
        if world.DEBUG > 3 : print("------------- we are over water")
        return True
    return False


class PythonInterface:
    def XPluginStart(self):
        self.Name = "ThermalSim2"
        self.Sig = "AlexFerrer.Python.ThermalSim2"
        self.Desc = "A plugin that simulates thermals (beta)"

        global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl

        # hot key for thermal visibility control 
        self.HotKey = xp.registerHotKey(xp.VK_F1, xp.DownFlag, "Says 'Hello World 1'", self.MyHotKeyCallback, 0)

        # ----- menu stuff --------------------------
        # init menu control params
        self.TCMenuItem = 0
        self.KK7MenuItem = 0
        self.CGMenuItem = 0
        self.StatsWindowItem = 0
        self.AboutMenuItem = 0

        global myMenu

        # Define the main menu items
        mySubMenuItem = xp.appendMenuItem(
            xp.findPluginsMenu(), "Thermal Simulator", 0, 1)
        self.MyMenuHandlerCB = self.MyMenuHandlerCallback
        self.myMenu = xp.createMenu("Thermals", xp.findPluginsMenu(), mySubMenuItem, self.MyMenuHandlerCB, 0)
        
        # No idea how to enable disable plugin.. maybe let it sit iddle ?
        xp.appendMenuItem(self.myMenu, "Disable Plugin ", activatePlugin, 1)
        xp.appendMenuItem(self.myMenu, "Generate Random Thermals", randomThermal, 1)
        xp.appendMenuItem(self.myMenu, "Load KK7 Thermals", csvThermal, 1)
        xp.appendMenuItem(self.myMenu, "Configure Glider", configGlider, 1)
        xp.appendMenuItem(self.myMenu, "Activate Stats Window", statsWindow, 1)
        xp.appendMenuItem(self.myMenu, "About", aboutThermal, 1)
        # -------------------------------------------------

        world.THERMAL_COLUMN_VISIBLE = True

        """ Data refs we want to record."""
        # airplane current flight info
        if world.DEBUG > 3 : print(" aircraft position")
        self.PlaneLat   = xp.findDataRef("sim/flightmodel/position/latitude")
        self.PlaneLon   = xp.findDataRef("sim/flightmodel/position/longitude")
        self.PlaneElev  = xp.findDataRef("sim/flightmodel/position/elevation")
        self.PlaneHdg   = xp.findDataRef("sim/flightmodel/position/psi")  # plane heading
        self.PlaneRol   = xp.findDataRef("sim/flightmodel/position/phi")  # plane roll
        self.PlanePitch = xp.findDataRef("sim/flightmodel/position/theta")  # plane pitch


        self.WindSpeed = xp.findDataRef(
            "sim/weather/wind_speed_kt[0]")  # wind speed at surface
        self.WindDir = xp.findDataRef(
            "sim/weather/wind_direction_degt[0]")  # wind direction

        # is the sim paused?
        self.runningTime = xp.findDataRef("sim/time/total_running_time_sec")
        self.sim_time = 0

        # sun pitch from flat in OGL coordinates degrees, for thermal strength calculation
        # from zero to 90 at 12pm in summer near the equator ..
        self.SunPitch = xp.findDataRef(
            'sim/graphics/scenery/sun_pitch_degrees')
        # temperature_sealevel_c
        # dewpoi_sealevel_c

        # terrain probe to test for height and water
        world.probe = xp.createProbe()
        world.terrain_is_water = xplane_terrain_is_water

        # variables to inject energy to the plane

        self.lift_Dref = xp.findDataRef('sim/flightmodel/forces/fnrml_plug_acf')
        self.roll_Dref = xp.findDataRef('sim/flightmodel/forces/L_plug_acf')
        self.pitch_Dref = xp.findDataRef('sim/flightmodel/forces/M_plug_acf')
                             
        # although lift should be enough, 
        # some energy has to go as thrust, or the plane
        # might float in the air without moving!
        #self.thrust = EasyDref('sim/flightmodel/forces/faxil_plug_acf', 'float')
        self.thrust_Dref = xp.findDataRef('sim/flightmodel/forces/faxil_plug_acf')
      
        # Drawing update flag
        world.world_update = True

        """
        Register our callback for once a second.  Positive intervals
        are in seconds, negative are the negative of sim frames.  Zero
        registers but does not schedule a callback for time.
        """
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 1.0, 0)
        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):    # Unregister the callbacks
        if world.DEBUG > 3 : print("XPPluginStop")
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)
 
        xp.destroyMenu(self.myMenu)
        # for probe suff
        xp.destroyProbe(world.probe)

    def XPluginEnable(self):
           return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def MyHotKeyCallback(self, inRefcon):
        # This is our hot key handler.  Note that we don't know what key stroke
        # was pressed!  We can identify our hot key by the 'refcon' value though.
        # This is because our hot key could have been remapped by the user and we
        # wouldn't know it.
        world.world_update = True
        world.THERMAL_COLUMN_VISIBLE = not world.THERMAL_COLUMN_VISIBLE
        print(" F1 Toggle thermal column visibility ",world.THERMAL_COLUMN_VISIBLE)

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        # the actual callback, runs once every x period as defined

        #If the plugin is disabled, skip the callback
        if world.PLUGIN_ENABLED == False:
            return 1    
        
        # is the sim paused? , then skip
        runtime = xp.getDataf(self.runningTime)
        if self.sim_time == runtime:
            print("P ", end='')
            return 1
        self.sim_time = runtime

        # instantiate the actual callbacks.
        if world.DEBUG > 5 : print("FlightLoop: Update xplane drefs : position,wind,sun")
        lat = xp.getDataf(self.PlaneLat)
        lon = xp.getDataf(self.PlaneLon)
        elevation = xp.getDataf(self.PlaneElev)
        heading = xp.getDataf(self.PlaneHdg)
        roll_angle = xp.getDataf(self.PlaneRol)
        pitch_angle = xp.getDataf(self.PlanePitch)

        # ----------------------------------------------------------
        # - REDUCE CALLS FOR THIS BLOCK TO REDUCE PERFORMANCE IMPACT   

        if world.update_loop > 100 :
            world.update_loop = 0 
            if world.DEBUG > 5: print("FlightLoop:  inside world update loop")

            #delay loading images until 100 cycles
            if world.images_loaded == False:
                           load_image_objects()
                           world.images_loaded = True
                           

            wind_speed = round(xp.getDataf(self.WindSpeed) *
                            0.5144, 2)      # Knots to m/s
            # Degrees to radians
            wind_dir = round(math.radians(xp.getDataf(self.WindDir)), 4)

            # sun pitch afects thermal power , noon in summer is the best..
            sun_pitch = xp.getDataf(self.SunPitch)  # Degrees
            world.sun_factor = (sun_pitch + 10)/100
            if sun_pitch < 0:
                world.sun_factor = 0

            # keep up with wind changes
            if [wind_speed, wind_dir] != [world.wind_speed, world.wind_dir]:
                if world.DEBUG > 4 : print( "wind changed [kt,deg], update world ",wind_speed,world.wind_speed,wind_dir,world.wind_dir)
                [world.wind_speed, world.wind_dir] = [wind_speed, wind_dir]
                world.world_update = True

            # Check if it is time to referesh the thermal map
            if ( (self.sim_time - world.thermal_map_start_time) > (world.thermal_refresh_time * 60) ) or len(world.thermal_list) == 0 :
                if world.DEBUG > 4: print("time is up , refreshing thermal map......................")
                lat = xp.getDataf(self.PlaneLat)
                lon = xp.getDataf(self.PlaneLon)
                world.thermal_list = make_random_thermal_map(self.sim_time,
                                                            lat, lon,
                                                            world.thermal_power,
                                                            world.thermal_density,
                                                            world.thermal_size)

                if world.DEBUG > 4 : print("request Update the world map") 
                world.world_update = True

            # if anything has changed updte the screen drawings
            if world.world_update:
                if world.DEBUG > 4: print("drawing thermals on screen")
                drawThermalsOnScreen(xp.getDataf(self.PlaneLat),
                                    xp.getDataf(self.PlaneLon)
                                    )
        #--------------------------------------------------        

        # Get the lift value of the current position from the world thermal map
        lift_val, roll_val, pitch_val = calc_thermalx(
            lat, lon, elevation, heading, roll_angle, pitch_angle)
        if world.DEBUG > 5: print("calc_thermal lift/roll/pitch",lift_val, roll_val,roll_val)

        # apply sun elevation as a % factor to thermal power
        # average lift depends on sun angle over the earth.
        lift_val = lift_val * world.sun_factor

        world.cal_lift_force = lift_val
        # apply the force to the airplanes lift.value dataref
        '''
        Calibrate feature
        set desired lift power in kts 
          trim the glider for flight straight and level at best glide speed. (100)
          measure the climb rate with the variometer 
          adjust +/- lift factor in newtons to match the desired lift power.
        '''
        # values for CALLBACKTIME = .01
        #     m/s @ kmh
        #   13 k  = 5 @ 95
        #   12.5k = 4 @ 90
        #   11k   = 2 @ 90
        #   10k   = 1 @ 90

        METERS_PER_SECOND_TO_NEWTON = 500 # 1m/s = 1000N
        if world.CALIBRATE_MODE:
           #lift (always)
           lift_amount =  METERS_PER_SECOND_TO_NEWTON *  world.lift_factor + xp.getDataf(self.lift_Dref)
           xp.setDataf(self.lift_Dref, lift_amount)
           lift = lift_amount

           #roll on pulse
           roll_amount = float(-200.0) * world.roll_factor
           roll = 0
           if world.roll_test_pulse > 0:
               world.roll_test_pulse -= 1
               xp.setDataf(self.roll_Dref, roll_amount)
               roll = roll_amount

           #pich on pulse
           pitch_amount = float(200.0) * world.pitch_factor
           pitch = 0
           if world.pitch_test_pulse > 0:
               world.pitch_test_pulse -= 1
               xp.setDataf(self.pitch_Dref, pitch_amount)
               pitch = pitch_amount

           world.message2  =  "Cal: L({:<10}) R({:<10}) P({:<10})".format(
               round(lift, 3), round(roll, 3), round(pitch, 3))

    
        else:
           # standart mode (non calibrate) 
           lval = lift_val * world.lift_factor * METERS_PER_SECOND_TO_NEWTON + xp.getDataf(self.lift_Dref)
           xp.setDataf(self.lift_Dref, lval)
           world.applied_lift_force = lval

           # apply a roll to the plane
           rval = roll_val * world.roll_factor + xp.getDataf(self.roll_Dref)
           xp.setDataf(self.roll_Dref, rval) 
           world.applied_roll_force = rval

           # apply a pitch to the plane
           pval = pitch_val * world.pitch_factor + xp.getDataf(self.pitch_Dref)
           xp.setDataf(self.pitch_Dref, pval) 
           world.applied_roll_force = pval

           world.message2  =  "Cal: L:{:<10} R:{:<10} P:{:<10}".format(
               round(lval, 3), round(rval, 3), round(pval, 3))


        # set the next callback time in +n for # of seconds and -n for # of Frames
        #return .01  # works good on my (pretty fast) machine..
        CALLBACKTIME = .01

        if world.DEBUG > 5:
            CALLBACKTIME = 5 # slow down for debugging
            print("next callback in second", CALLBACKTIME)

        world.update_loop += 1
        return CALLBACKTIME

    # --------------------------------------------------------------------------------------------------
    #                     UI &  M E N U   S T U F F
    # --------------------------------------------------------------------------------------------------

    def MyMenuHandlerCallback(self, inMenuRef, inItemRef):

        # activate / deactivate  plugin
        if (inItemRef == activatePlugin):
            if world.PLUGIN_ENABLED :
                xp.setMenuItemName(menuID=self.myMenu, index=activatePlugin, name='Enable Plugin')
                world.PLUGIN_ENABLED = False
                eraseThermalsRingsOnScreen()
                eraseThermalsCloudsOnScreen()
                world.thermal_list = []
            else:
                xp.setMenuItemName(menuID=self.myMenu, index=activatePlugin, name='Disable Plugin')
                world.PLUGIN_ENABLED = True

        # Open stats window
        if (inItemRef == statsWindow):
            print("Open Stats Window")
            self.WindowId = xp.createWindowEx(50, 600, 300, 400, 1,
                                self.DrawWindowCallback,
                                None,
                                None,
                                None,
                                None,
                                0,
                                xp.WindowDecorationRoundRectangle,
                                xp.WindowLayerFloatingWindows,
                                None)

        #--------------------------------
        if (inItemRef == randomThermal):
            print("show thermal config box ")
            if (self.TCMenuItem == 0):
                print(" create the thermal config box ")
                self.CreateTCWindow(100, 600, 600, 400)
                self.TCMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.TCWidget)):
                    print("re-show Thermal config box ")
                    xp.showWidget(self.TCWidget)
 
        if (inItemRef == csvThermal):
            print("Making thermals from list")
            if (self.KK7MenuItem == 0):
                print(" create the KK7 thermal config box ")
                self.CreateKK7Window(100, 550, 550, 330)
                self.KK7MenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.KK7Widget)):
                    print("re-show KK7 config box ")
                    xp.showWidget(self.KK7Widget)

        if (inItemRef == configGlider):
            print("show Glider config box ")
            if (self.CGMenuItem == 0):
                print(" create the Glider config box ")
                self.CreateCGWindow(100, 550, 550, 330)
                self.CGMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.CGWidget)):
                    print("re-show Glider config box ")
                    xp.showWidget(self.CGWidget)

        print("menu option ------>", inItemRef)
        if (inItemRef == aboutThermal):
            print("show about box ")
            if (self.AboutMenuItem == 0):
                print(" create the About box ")
                self.CreateAboutWindow(100, 550, 460, 380)
                self.AboutMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.AboutWidget)):
                    print("re-show about box ")
                    xp.showWidget(self.AboutWidget)

    ''' Menu windows defined on their own files for clarity. 
    '''
    # Configure Thermals
    from thermalsUI import TCHandler
    from thermalsUI import CreateTCWindow

    # About Window
    from aboutUI import CreateAboutWindow
    from aboutUI import AboutHandler

    # Config Glider UI
    from configGlider import CGHandler
    from configGlider import CreateCGWindow

    # Load KK7  UI
    from kk7UI import KK7Handler
    from kk7UI import CreateKK7Window

    # ------- after this debug

    """
    MyDrawingWindowCallback

    This callback does the work of drawing our window once per sim cycle each time
    it is needed.  It dynamically changes the text depending on the saved mouse
    status.  Note that we don't have to tell X-Plane to redraw us when our text
    changes; we are redrawn by the sim continuously.
    """
    def DrawWindowCallback(self, inWindowID, inRefcon):
        # First we get the location of the window passed in to us.
        (left, top, right, bottom) = xp.getWindowGeometry(inWindowID)
        """
        We now use an XPLMGraphics routine to draw a translucent dark
        rectangle that is our window's shape.
        """
        xp.drawTranslucentDarkBox(left, top, right, bottom)
        color = 1.0, 1.0, 1.0
        RED = 1.0, 0.0, 0.0
        GREEN = 0.0, 1.0, 0.0
        """
        Finally we draw the text into the window, also using XPLMGraphics
        routines.  The NULL indicates no word wrapping.
        """
        if world.thermal_radius > world.distance_from_center:
           xp.drawString(GREEN, left + 90, top - 20, "IN THERMAL", 0, xp.Font_Basic)

           xp.drawString(color, left + 5, top - 125, "T Lift :"+ str(round(world.tot_lift_force, 2)) +"m/s", 0, xp.Font_Basic)
           xp.drawString(GREEN, left + 99, top - 125, "% "+ str(round(world.cal_lift_force, 2)) +"m/s", 0, xp.Font_Basic)

           xp.drawString(color, left + 5, top - 145,  "T Roll :"+ str(round(world.tot_roll_force, 2) )+"N", 0, xp.Font_Basic)
           xp.drawString(color, left + 99, top - 145, "% "+ str(round(world.applied_roll_force, 2) )+"N", 0, xp.Font_Basic)


           xp.drawString(GREEN, left + 5, top -160, "Applied: "+ str(round(world.applied_lift_force, 2)) +"N", 0, xp.Font_Basic)
        else:
            xp.drawString(RED, left + 90, top - 20, "OFF THERMAL", 0, xp.Font_Basic)

        dfc = str(round(world.distance_from_center, 2))
        xp.drawString(color, left + 80, top - 35,  "Distance   : "+ dfc +"m", 0, xp.Font_Basic)
        xp.drawString(color, left + 80, top - 50,  "T Radius   : "+ str(round(world.thermal_radius,2) )+"m", 0, xp.Font_Basic)
        xp.drawString(color, left + 80, top - 65,  "T Strength : "+ str(round(world.thermal_strength,2)) +" m/s", 0, xp.Font_Basic)
        xp.drawString(color, left + 80, top - 90,  "Lfactor: "+ str(round(world.lift_factor, 2)) +"X", 0, xp.Font_Basic)
        xp.drawString(color, left + 80, top - 105, "Rfactor: "+ str(round(world.roll_factor, 2)) +"X", 0, xp.Font_Basic)
        


        xp.drawString(color, left + 5, top - 170, "["+world.message+"]", 0, xp.Font_Basic)
        xp.drawString(GREEN, left + 5, top - 180, "["+world.message1+"]", 0, xp.Font_Basic)
        xp.drawString(color, left + 5, top - 190, "["+world.message2+"]", 0, xp.Font_Basic)
