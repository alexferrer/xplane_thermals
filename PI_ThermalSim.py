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
from thermal_model import calc_thermalx
from thermal_model import make_random_thermal_map

from draw_thermals import drawThermalsOnScreen, eraseThermalsCloudsOnScreen, eraseThermalsRingsOnScreen, load_image_objects

import random
from random import randrange
import math

import xp
from XPPython3.xp_typing import *

from XPPython3 import xp_imgui # type: ignore
import imgui  # type: ignore

#########################################################

# ------------------  T H E R M A L   S I M U L A T O R  ----------------------------

activatePlugin = 0
toggleThermal = 1
randomThermal = 2
csvThermal = 3
aboutThermal = 4
configGlider = 5
statsWindow = 6

class PythonInterface:

    def __init__(self):
        # init menu control params
        self.KK7MenuItem = 0
        self.CGMenuItem = 0
        self.StatsWindowItem = 0
        self.AboutMenuItem = 0
        self.TCMenuItem = 0
        global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl
        global myMenu


    def XPluginStart(self):
        self.Name = "ThermalSim2"
        self.Sig = "AlexFerrer.Python.ThermalSim2"
        self.Desc = "A plugin that simulates thermals (beta)"

        # hot key for thermal visibility control 
        self.HotKey = xp.registerHotKey(xp.VK_F1, xp.DownFlag, "Says 'Hello World 1'", self.MyHotKeyCallback, 0)

        # ----- menu stuff --------------------------
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
        
        # Define an XPlane command 
        # It may be called from a menu item, a key stroke, or a joystick button
        self.commmandRef = xp.createCommand('alexferrer/xplane_thermals/show_thermal_rings', 'on/off thermal rings')
        xp.registerCommandHandler(self.commmandRef, self.CommandHandler)

        
        
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
        world.sim_time = 0

        # sun pitch from flat in OGL coordinates degrees, for thermal strength calculation
        # from zero to 90 at 12pm in summer near the equator ..
        self.SunPitch = xp.findDataRef(
            'sim/graphics/scenery/sun_pitch_degrees')
        # temperature_sealevel_c
        # dewpoi_sealevel_c

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
        world.save_init_values()

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

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        # the actual callback, runs once every x period as defined

        if not world.KK7_WINDOW_OPEN :
           self.close_KK7_Window()
           world.KK7_WINDOW_OPEN = True

        #If the plugin is disabled, skip the callback
        if world.PLUGIN_ENABLED == False:
            return 1    
        
        # is the sim paused? , then skip
        runtime = xp.getDataf(self.runningTime)
        if world.sim_time == runtime:
            print("P ", end='')
            return 1
        world.sim_time = runtime
      
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
            if ( (world.sim_time - world.thermal_map_start_time) > (world.thermal_refresh_time * 60) ) or len(world.thermal_list) == 0 :
                if world.DEBUG > 4: print("time is up , refreshing thermal map......................")
                lat = xp.getDataf(self.PlaneLat)
                lon = xp.getDataf(self.PlaneLon)
                world.thermal_list = make_random_thermal_map(world.sim_time,
                                                            lat, lon,
                                                            world.thermal_power,
                                                            world.thermal_density,
                                                            world.thermal_size)
                if world.DEBUG > 4 : print("request Update the world map") 
                world.world_update = True

            # if anything has changed updte the screen drawings
            if world.world_update:
                if world.DEBUG > 2: print("main-> calling drawThermalsOnScreen")
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

        METERS_PER_SECOND_TO_NEWTON = 10 # 1m/s = 1000N
        if world.CALIBRATE_MODE:
           #fake lift value  = 1 m/s
           lift_val = 1

           lift =  lift_val* METERS_PER_SECOND_TO_NEWTON *  world.lift_factor + xp.getDataf(self.lift_Dref)
           xp.setDataf(self.lift_Dref, lift)

           thrust_val = lift_val  # same as lift for now 

           thrust =  -1 * thrust_val * METERS_PER_SECOND_TO_NEWTON * world.thrust_factor + xp.getDataf(self.thrust_Dref)
           xp.setDataf(self.thrust_Dref, thrust)

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

           world.message2  =  "Cal: L({:<5}) T({:<5}) R({:<4}) P({:<4})".format(
               round(lift, 1), round(thrust, 1), round(roll, 1), round(pitch, 1))

           world.message  =  "Fac: L({:<5}) T({:<5}) R({:<4}) P({:<4})".format(
               round(world.lift_factor, 1), round(world.thrust_factor, 1), round(world.roll_factor, 1), round(world.pitch_factor, 1))

        else:
           # standart mode (non calibrate) 
           lift = lift_val * METERS_PER_SECOND_TO_NEWTON * world.lift_factor + xp.getDataf(self.lift_Dref)
           xp.setDataf(self.lift_Dref, lift)
           world.applied_lift_force = lift

           thrust_val = lift_val  # same as lift for now
           thrust = -1 * thrust_val * METERS_PER_SECOND_TO_NEWTON * world.thrust_factor + xp.getDataf(self.thrust_Dref)
           xp.setDataf(self.thrust_Dref, thrust)
           world.applied_thrust_force = thrust

           # apply a roll to the plane
           roll = roll_val * world.roll_factor + xp.getDataf(self.roll_Dref)
           xp.setDataf(self.roll_Dref, roll) 
           world.applied_roll_force = roll

           # apply a pitch to the plane
           pitch = pitch_val * world.pitch_factor + xp.getDataf(self.pitch_Dref)
           xp.setDataf(self.pitch_Dref, pitch) 
           world.applied_pitch_force = pitch

           world.message2  =  "Cal: L({:<6}) T({:<6}) R({:<4}) P({:<4})".format(
               round(lift, 1), round(thrust, 1), round(roll, 1), round(pitch, 1))

           world.message  =  "Fac: L({:<5}) T({:<5}) R({:<4}) P({:<4})".format(
               round(world.lift_factor, 1), round(world.thrust_factor, 1), round(world.roll_factor, 1), round(world.pitch_factor, 1))



        # set the next callback time in +n for # of seconds and -n for # of Frames
        #return .01  # works good on my (pretty fast) machine..
        CALLBACKTIME = .01

        if world.DEBUG > 5:
            CALLBACKTIME = 3 # slow down for debugging
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
                world.save_init_values()
            else:
                xp.setMenuItemName(menuID=self.myMenu, index=activatePlugin, name='Disable Plugin')
                world.PLUGIN_ENABLED = True
                world.save_init_values()

        # Open stats window
        if (inItemRef == statsWindow):
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
            if (self.TCMenuItem == 0):
                self.CreateTCWindow(100, 600, 600, 400)
                self.TCMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.TCWidget)):
                    xp.showWidget(self.TCWidget)
 
        if (inItemRef == csvThermal):
            if world.DEBUG > 1 : print("csvThermal: Menu kk7Thermal  kk7menuitem->") 
            self.create_CSV_Window()
 
        if (inItemRef == configGlider):
            if (self.CGMenuItem == 0):
                self.CreateCGWindow(100, 550, 550, 400)
                self.CGMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.CGWidget)):
                    xp.showWidget(self.CGWidget)

        if (inItemRef == aboutThermal):
            if (self.AboutMenuItem == 0):
                self.CreateAboutWindow(100, 550, 460, 380)
                self.AboutMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.AboutWidget)):
                    xp.showWidget(self.AboutWidget)

    ''' Menu windows defined on their own files for clarity. 
    '''
    # Configure Thermals
    from UI_thermals import TCHandler
    from UI_thermals import CreateTCWindow

    # About Window
    from UI_about import CreateAboutWindow
    from UI_about import AboutHandler

    # Config Glider UI
    from UI_config_glider import CGHandler
    from UI_config_glider import CreateCGWindow

    # Load KK7  UI
    from UI_load_kk7 import loadHotspots , retrieveCSVFiles, create_CSV_Window, draw_CSV_Window, close_KK7_Window

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


    def CommandHandler(self, commandRef, phase, refCon):
        print(f"Command got phase: {phase}")
        if phase == xp.CommandBegin:
            world.THERMAL_COLUMN_VISIBLE = not world.THERMAL_COLUMN_VISIBLE
            world.world_update = True
            print(" Toggle thermal column visibility ",world.THERMAL_COLUMN_VISIBLE)

        elif phase == xp.CommandContinue:
            print("Command Continue")
        elif phase == xp.CommandEnd:
            print("Command End")
        return 1
