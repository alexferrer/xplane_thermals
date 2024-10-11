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

from draw_thermals import drawThermalsOnScreen, eraseThermalsOnScreen

import random
from random import randrange
import math

import xp
from XPPython3.xp_typing import *

#########################################################

# ------------------  T H E R M A L   S I M U L A T O R  ----------------------------
LIB_VERSION = "Version ----------------------------   PI_ThermalSim V2.0"
print(LIB_VERSION)

toggleThermal = 1
randomThermal = 2
csvThermal = 3
aboutThermal = 4
configGlider = 5

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
        global gOutputFile, gPlaneLat, gPlaneLon, gPlaneEl

        # ----- menu stuff --------------------------
        # init menu control params
        self.TCMenuItem = 0
        self.CSVMenuItem = 0
        self.CGMenuItem = 0
        self.AboutMenuItem = 0

        global myMenu

        # Define the main menu items
        mySubMenuItem = xp.appendMenuItem(
            xp.findPluginsMenu(), "Thermal Simulator", 0, 1)
        self.MyMenuHandlerCB = self.MyMenuHandlerCallback
        self.myMenu = xp.createMenu(
            "Thermals", xp.findPluginsMenu(), mySubMenuItem, self.MyMenuHandlerCB, 0)
        xp.appendMenuItem(
            self.myMenu, "Generate Random Thermals", randomThermal, 1)
        #xp.appendMenuItem(self.myMenu, "Load KK7 Thermals for CSV", csvThermal, 1)
        xp.appendMenuItem(self.myMenu, "Configure Glider", configGlider, 1)
        xp.appendMenuItem(self.myMenu, "About", aboutThermal, 1)


        # -------------------------------------------------
        if world.DEBUG > 3 : print("setting up global variables")
        world.THERMAL_COLUMN_VISIBLE = True
        self.Name = "ThermalSim2"
        self.Sig = "AlexFerrer.Python.ThermalSim2"
        self.Desc = "A plugin that simulates thermals (beta)"

        """ Data refs we want to record."""
        # airplane current flight info
        if world.DEBUG > 3 : print(" aircraft position")
        self.PlaneLat = xp.findDataRef("sim/flightmodel/position/latitude")
        self.PlaneLon = xp.findDataRef("sim/flightmodel/position/longitude")
        self.PlaneElev = xp.findDataRef("sim/flightmodel/position/elevation")
        self.PlaneHdg = xp.findDataRef("sim/flightmodel/position/psi")  # plane heading
        self.PlaneRol = xp.findDataRef("sim/flightmodel/position/phi")  # plane roll

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

                             
        # although lift should be enough, some energy has to go as thrust, or the plane
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
        if world.DEBUG > 3 : print("registering callback")
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 1.0, 0)

        #------------------------------
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
        #--------------

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

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        #if world.DEBUG: print("start the FlightLoopCallback ")
        # the actual callback, runs once every x period as defined

        # is the sim paused? , then skip
        runtime = xp.getDataf(self.runningTime)
        if self.sim_time == runtime:
            print("P ", end='')
            return 1
        self.sim_time = runtime

        # instantiate the actual callbacks.
        if world.DEBUG > 5 : print(" Update position,wind,sun")
        lat = xp.getDataf(self.PlaneLat)
        lon = xp.getDataf(self.PlaneLon)
        elevation = xp.getDataf(self.PlaneElev)
        heading = xp.getDataf(self.PlaneHdg)
        roll_angle = xp.getDataf(self.PlaneRol)

        # ----------------------------------------------------------
        # - REDUCE CALLS FOR THIS BLOCK TO REDUCE PERFORMANCE IMPACT
        

        if world.update_loop > 100 :
            world.update_loop = 0 
            if world.DEBUG > 5: print("world update loop")


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
        lift_val, roll_val = calc_thermalx(
            lat, lon, elevation, heading, roll_angle)
        if world.DEBUG > 5: print("calc_thermal lift/roll",lift_val, roll_val)

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

        METERS_PER_SECOND_TO_NEWTON = 5000 # 1m/s = 1000N
        if world.CALIBRATE_MODE:
           amount =  METERS_PER_SECOND_TO_NEWTON *  world.lift_factor + xp.getDataf(self.lift_Dref)
           xp.setDataf(self.lift_Dref, amount)
           world.applied_lift_force = amount

        else:
           lval = lift_val * world.lift_factor * METERS_PER_SECOND_TO_NEWTON + xp.getDataf(self.lift_Dref)
           xp.setDataf(self.lift_Dref, lval)
           world.applied_lift_force = lval

        # although extra lift is what should be happening...
        # adding a bit of thrust works much better! -150 = 1m/s
        # apply a max thurst to a factor of 500fpm
        #ALX maybe i should use pitch down instead of thrust ?
        tval = xp.getDataf(self.thrust_Dref)
        new_tvalue = (- world.thrust_factor) * lift_val + tval 
        #ALX xp.setDataf(self.thrust_Dref, new_tvalue) 


        # apply a roll to the plane
        if world.CALIBRATE_MODE:
            roll_amount = float(-200.0) * world.roll_factor
            if world.roll_test_pulse > 0:
               world.roll_test_pulse -= 1
               xp.setDataf(self.roll_Dref, roll_amount)
               if world.DEBUG > 4: print("apply roll to the plane [roll factor/tot]",world.roll_factor ,roll_amount,world.roll_test_pulse)
        else:
           rval = roll_val * world.roll_factor + xp.getDataf(self.roll_Dref)
           xp.setDataf(self.roll_Dref, rval) 
           world.applied_roll_force = rval


        # set the next callback time in +n for # of seconds and -n for # of Frames
        CALLBACKTIME = .01

        if world.DEBUG > 5: CALLBACKTIME = 5 # slow down for debugging
        if world.DEBUG > 5: print("next callback in second", CALLBACKTIME)
        world.update_loop += 1
        #return .01  # works good on my (pretty fast) machine..
        return CALLBACKTIME

    # --------------------------------------------------------------------------------------------------

    #                        M E N U   S T U F F

    # ------------------------------------ menu stuff  from here on ----------------------------------

    def MyMenuHandlerCallback(self, inMenuRef, inItemRef):

        if (inItemRef == randomThermal):
            print("show thermal config box ")
            if (self.TCMenuItem == 0):
                print(" create the thermal config box ")
                self.CreateTCWindow(100, 600, 600, 400)
                self.TCMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.TCWidget)):
                    print("re-show test config box ")
                    xp.showWidget(self.TCWidget)
 
        if (inItemRef == csvThermal):
            print("Making thermals from list")
            if (self.CSVMenuItem == 0):
                print(" create the thermal config box ")
                self.CreateCSVWindow(100, 550, 550, 330)
                self.CSVMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.CSVWidget)):
                    print("re-show test config box ")
                    xp.showWidget(self.CSVWidget)

        if (inItemRef == configGlider):
            print("show thermal config box ")
            if (self.CGMenuItem == 0):
                print(" create the thermal config box ")
                self.CreateCGWindow(100, 550, 550, 330)
                self.CGMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.CGWidget)):
                    print("re-show test config box ")
                    xp.showWidget(self.CGWidget)

        print("menu option ------>", inItemRef)
        if (inItemRef == aboutThermal):
            print("show about box ")
            if (self.AboutMenuItem == 0):
                print(" create the thermal config box ")
                self.CreateAboutWindow(100, 550, 450, 230)
                self.AboutMenuItem = 1
            else:
                if(not xp.isWidgetVisible(self.AboutWidget)):
                    print("re-show about box ")
                    xp.showWidget(self.AboutWidget)

    def TCHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xp.Message_CloseButtonPushed):
            print("close button pushed")
            if (self.TCMenuItem == 1):
                print("hide the widget")
                xp.hideWidget(self.TCWidget)
                return 1

        # Process when a button on the widget is pressed
        if (inMessage == xp.Msg_PushButtonPressed):
            print("[button was pressed", inParam1, "]")

            # Tests the Command API, will find command
            if (inParam1 == self.TGenerate_button):
                print("Menu: Generate Thermas")
                print("minimum separation between thermals :", world.thermal_distance)
                lat = xp.getDataf(self.PlaneLat)
                lon = xp.getDataf(self.PlaneLon)
                #world.cloud_streets = xp.getWidgetProperty(self.enableCheck, xp.Property_ButtonState, None)
                #print("enable cloud streets", world.cloud_streets)
                # lat,lon,stregth,count
                world.thermal_list = make_random_thermal_map(self.sim_time,
                                                             lat, lon,
                                                             world.thermal_power,
                                                             world.thermal_density,
                                                             world.thermal_size)
                world.world_update = True
                world.update_loop = 101
                return 1

        if (inMessage == xp.Msg_ButtonStateChanged):
            world.THERMAL_COLUMN_VISIBLE = xp.getWidgetProperty(
                self.enableCheck, xp.Property_ButtonState, None)
            world.world_update = True
            print(" Toggle thermal column visibility ",world.THERMAL_COLUMN_VISIBLE)

        if (inMessage == xp.Msg_ScrollBarSliderPositionChanged):
            # Thermal Tops
            val = xp.getWidgetProperty(
                self.TTops_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TTops_value, str(val))
            world.thermal_tops = int(val * world.f2m)

            # Thermal Density
            val = xp.getWidgetProperty(
                self.TDensity_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TDensity_value, str(val))
            world.thermal_density = val

            # Minimum Distance Between  Thermals
            val = xp.getWidgetProperty(
                self.TDistance_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TDistance_value, str(val))
            world.thermal_distance = val

            # Thermals refresh time
            val = xp.getWidgetProperty(
                self.TRefresh_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TRefresh_value, str(val))
            world.thermal_refresh_time = val

            # Thermal Size
            val = xp.getWidgetProperty(
                self.TSize_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TSize_value, str(val))
            world.thermal_size = val

            # Thermal Power
            val = xp.getWidgetProperty(
                self.TPower_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TPower_value, str(val))
            world.thermal_power = val

            # Thermal Cycle
            val = xp.getWidgetProperty(
                self.TCycle_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TCycle_value, str(val))
            world.thermal_cycle = val

        return 0

    # Creates the widget with buttons for test and edit boxes for info

    def CreateTCWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "Thermal Generator Configuration"

        # create the window
        self.TCWidget = xp.createWidget(
            x, y, x2, y2, 1, Title, 1,     0, xp.WidgetClass_MainWindow)
        xp.setWidgetProperty(
            self.TCWidget, xp.Property_MainWindowHasCloseBoxes, 1)
        TCWindow = xp.createWidget(
            x+50, y-50, x2-50, y2+50, 1, "",     0, self.TCWidget, xp.WidgetClass_SubWindow)
        xp.setWidgetProperty(TCWindow, xp.Property_SubWindowType,
                             xp.SubWindowStyle_SubWindow)

        # -----------------------------
        # Thermal Tops
        self.TTops_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermals Tops", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TTops_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Feet", 0, self.TCWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.TTops_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TTops_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TTops_scrollbar,
                             xp.Property_ScrollBarMin, 100)
        xp.setWidgetProperty(self.TTops_scrollbar,
                             xp.Property_ScrollBarMax, 20000)
        xp.setWidgetProperty(self.TTops_scrollbar,
                             xp.Property_ScrollBarPageAmount, 500)
        xp.setWidgetProperty(self.TTops_scrollbar, xp.Property_ScrollBarSliderPosition, int(
            world.thermal_tops*world.m2f))
        xp.setWidgetDescriptor(self.TTops_value, str(
            int(world.thermal_tops*world.m2f)))
        y -= 32

        # Thermal Distance
        self.TDistance_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "T. Separation", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TDistance_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Meters", 0, self.TCWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.TDistance_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TDistance_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TDistance_scrollbar,
                             xp.Property_ScrollBarMin, 200)
        xp.setWidgetProperty(self.TDistance_scrollbar,
                             xp.Property_ScrollBarMax, 10000)
        xp.setWidgetProperty(self.TDistance_scrollbar,
                             xp.Property_ScrollBarPageAmount, 100)
        xp.setWidgetProperty(self.TDistance_scrollbar, xp.Property_ScrollBarSliderPosition, int(
            world.thermal_distance))
        xp.setWidgetDescriptor(self.TDistance_value,
                               str(int(world.thermal_distance)))
        y -= 32

        # Thermal map Refresh time
        self.TRefresh_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermals Refresh", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TRefresh_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Minutes", 0, self.TCWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.TRefresh_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TRefresh_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TRefresh_scrollbar,
                             xp.Property_ScrollBarMin, 10)
        xp.setWidgetProperty(self.TRefresh_scrollbar,
                             xp.Property_ScrollBarMax, 200)
        xp.setWidgetProperty(self.TRefresh_scrollbar,
                             xp.Property_ScrollBarPageAmount, 20)
        xp.setWidgetProperty(self.TRefresh_scrollbar, xp.Property_ScrollBarSliderPosition, int(
            world.thermal_refresh_time))
        xp.setWidgetDescriptor(self.TRefresh_value, str(
            int(world.thermal_refresh_time)))
        y -= 32

        # Thermal Density
        self.TDensity_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Density", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TDensity_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "# of Thermals", 0, self.TCWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.TDensity_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TDensity_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TDensity_scrollbar,
                             xp.Property_ScrollBarMin, 10)
        xp.setWidgetProperty(self.TDensity_scrollbar,
                             xp.Property_ScrollBarMax, 500)
        xp.setWidgetProperty(self.TDensity_scrollbar,
                             xp.Property_ScrollBarPageAmount, 10)
        xp.setWidgetProperty(self.TDensity_scrollbar,
                             xp.Property_ScrollBarSliderPosition, world.thermal_density)
        xp.setWidgetDescriptor(self.TDensity_value, str(world.thermal_density))
        y -= 32

        # Thermal Size
        self.TSize_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Size", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TSize_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max Diameter m", 0, self.TCWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.TSize_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TSize_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TSize_scrollbar, xp.Property_ScrollBarMin, 50)
        xp.setWidgetProperty(self.TSize_scrollbar,
                             xp.Property_ScrollBarMax, 3000)
        xp.setWidgetProperty(self.TSize_scrollbar,
                             xp.Property_ScrollBarPageAmount, 20)
        xp.setWidgetProperty(
            self.TSize_scrollbar, xp.Property_ScrollBarSliderPosition, world.thermal_size)
        xp.setWidgetDescriptor(self.TSize_value, str(world.thermal_size))
        y -= 32

        # Thermal Strength
        self.TPower_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal m/s", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TPower_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "m/s average", 0, self.TCWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.TPower_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TPower_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TPower_scrollbar,
                             xp.Property_ScrollBarMin, 1)
        xp.setWidgetProperty(self.TPower_scrollbar,
                             xp.Property_ScrollBarMax, 15)
        xp.setWidgetProperty(self.TPower_scrollbar,
                             xp.Property_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(
            self.TPower_scrollbar, xp.Property_ScrollBarSliderPosition, world.thermal_power)
        xp.setWidgetDescriptor(self.TPower_value, str(world.thermal_power))
        y -= 32

        # Thermal Cycle time
        self.TCycle_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Cycle Time", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TCycle_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Minutes", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TCycle_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget,  xp.WidgetClass_Caption)
        self.TCycle_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TCycle_scrollbar, xp.Property_ScrollBarMin, 5)
        xp.setWidgetProperty(self.TCycle_scrollbar,
                             xp.Property_ScrollBarMax, 90)
        xp.setWidgetProperty(self.TCycle_scrollbar,
                             xp.Property_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(
            self.TCycle_scrollbar, xp.Property_ScrollBarSliderPosition, world.thermal_cycle)
        xp.setWidgetDescriptor(self.TCycle_value, str(world.thermal_cycle))
        y -= 30

        # Define checkbox for thermal column visibility
        xp.createWidget(x+60, y-80, x+140, y-102, 1, 'Thermal Column Visible',
                        0, self.TCWidget,  xp.WidgetClass_Caption)
        self.enableCheck = xp.createWidget(
            x+220, y-80, x+260, y-102, 1, '', 0, self.TCWidget, xp.WidgetClass_Button)
        xp.setWidgetProperty(
            self.enableCheck, xp.Property_ButtonType, xp.RadioButton)
        xp.setWidgetProperty(
            self.enableCheck, xp.Property_ButtonBehavior, xp.ButtonBehaviorCheckBox)
        xp.setWidgetProperty(
            self.enableCheck, xp.Property_ButtonState, world.THERMAL_COLUMN_VISIBLE)
        y -= 75

        # define button
        self.TGenerate_button = xp.createWidget(x+320, y-60, x+440, y-82,
                                                1, "Generate Thermals", 0, self.TCWidget, xp.WidgetClass_Button)
        xp.setWidgetProperty(self.TGenerate_button,
                             xp.Property_ButtonType, xp.PushButton)

        # --------------------------
        self.TCHandlerCB = self.TCHandler
        xp.addWidgetCallback(self.TCWidget, self.TCHandlerCB)


# ----------------------- About Window


    def CreateAboutWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "About Thermal Simulator"

        # create the window
        self.AboutWidget = xp.createWidget(
            x, y, x2, y2, 1, Title, 1,     0, xp.WidgetClass_MainWindow)
        xp.setWidgetProperty(
            self.AboutWidget, xp.Property_MainWindowHasCloseBoxes, 1)
        AboutWindow = xp.createWidget(
            x+50, y-50, x2-50, y2+50, 1, "",     0, self.AboutWidget, xp.WidgetClass_SubWindow)
        xp.setWidgetProperty(
            AboutWindow, xp.Property_SubWindowType, xp.SubWindowStyle_SubWindow)

        text1 = "Thermal Simulator for Python 3"
        self.About_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, text1, 0, self.AboutWidget, xp.WidgetClass_Caption)
        y -= 35

        text2 = "Author: Alex Ferrer  @ 2014, 2022"
        self.About_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, text2, 0, self.AboutWidget, xp.WidgetClass_Caption)
        y -= 35

        text3 = " https://github.com/alexferrer/xplane_thermals/wiki"
        self.About_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, text3, 0, self.AboutWidget,  xp.WidgetClass_Caption)
        y -= 45

        #------
        # Set debug level 
        self.DBug_label1 = xp.createWidget(
            x+50,  y-80, x+140, y-102, 1, "Debug Setting    Min", 0, self.AboutWidget,  xp.WidgetClass_Caption)
        self.DBug_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max", 0, self.AboutWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.DBug_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.AboutWidget,  xp.WidgetClass_Caption)
        self.DBug_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.AboutWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.DBug_scrollbar,
                             xp.Property_ScrollBarMin, 0)
        xp.setWidgetProperty(self.DBug_scrollbar,
                             xp.Property_ScrollBarMax, 10)
        xp.setWidgetProperty(self.DBug_scrollbar,
                             xp.Property_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(self.DBug_scrollbar, xp.Property_ScrollBarSliderPosition, int(
            world.DEBUG))
        xp.setWidgetDescriptor(self.DBug_value, str(
            int(world.DEBUG)))
        y -= 32
        #------
        self.AboutHandlerCB = self.AboutHandler
        xp.addWidgetCallback(self.AboutWidget, self.AboutHandlerCB)
     # ----

    def AboutHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xp.Message_CloseButtonPushed ):
            print("about close button pushed")
            if (self.AboutMenuItem == 1):
                print("hide the widget")
                xp.hideWidget(self.AboutWidget)
                return 1
        if (inMessage == xp.Msg_ScrollBarSliderPositionChanged):
            # Thermal Tops
            val = xp.getWidgetProperty(
                self.DBug_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.DBug_value, str(val))
            world.DEBUG = int(val * world.f2m)

        return 0
# ----------------------------------------- new...

    def CGHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xp.Message_CloseButtonPushed):
            print("config glider window close button pushed")
            world.CALIBRATE_MODE = False
            if (self.CGMenuItem == 1):
                print("hide the widget")
                xp.hideWidget(self.CGWidget)
                return 1
        # Process when a radiobutton on the widget is pressed
        if (inMessage == xp.Msg_ButtonStateChanged):
            world.CALIBRATE_MODE = xp.getWidgetProperty(
                self.enableCheck1, xp.Property_ButtonState, None)
            print(" CALIBRATE_MODE ", world.CALIBRATE_MODE)

        # Process button on the widget is pressed
        if (inMessage ==  xp.Msg_PushButtonPressed):
            print("[button was pressed", inParam1, "]")

            # Tests the Command API, will find command
            if (inParam1 == self.CGGenerate_button):
                print("Generate")
                return 1

            if (inParam1 == self.CGRandom_button):
                print("Glider Config: roll wing left")
                # roll for 100 units
                world.roll_test_pulse = 50
                return 1
        # Process when a scrollbar on the widget is changed
        if (inMessage == xp.Msg_ScrollBarSliderPositionChanged):
            # Lift Factor
            val = xp.getWidgetProperty(
                self.CGLift_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CGLift_value, str(val))
            world.lift_factor = val * .1

            # Thrust Factor
            val = xp.getWidgetProperty(
                self.CGThrust_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CGThrust_value, str(val))
            world.thrust_factor = val * .1

            # Roll factor
            val = xp.getWidgetProperty(
                self.CGRoll_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CGRoll_value, str(val))
            world.roll_factor = val

            # Wing Size
            val = xp.getWidgetProperty(
                self.CGWing_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CGWing_value, str(val))
            world.wing_size = val

        return 0

    # Creates the config glider widget

    def CreateCGWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "Glider Energy Configuration"

        # create the window
        self.CGWidget = xp.createWidget(
            x, y, x2, y2, 1, Title, 1,     0, xp.WidgetClass_MainWindow)
        xp.setWidgetProperty(
            self.CGWidget, xp.Property_MainWindowHasCloseBoxes, 1)
        CGWindow = xp.createWidget(
            x+50, y-50, x2-50, y2+50, 1, "",     0, self.CGWidget, xp.WidgetClass_SubWindow)
        xp.setWidgetProperty(CGWindow, xp.Property_SubWindowType,
                             xp.SubWindowStyle_SubWindow)

        # -----------------------------
        # Lift Component
        CGLift_message0 = "Trim the glider for flight straight and level at best glide speed."
        CGLift_message1 = "Adjust the lift factor until vario shows 1m/s Vs"
        self.CGLift_label_a = xp.createWidget(
            x+80,  y-20, x+140, y-35, 1, CGLift_message0, 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGLift_label_b = xp.createWidget(
            x+110,  y-30, x+140, y-60, 1, CGLift_message1, 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGLift_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Lift Factor", 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGLift_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Units", 0, self.CGWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.CGLift_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGLift_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CGLift_scrollbar, xp.Property_ScrollBarMin, 0)
        xp.setWidgetProperty(self.CGLift_scrollbar,
                             xp.Property_ScrollBarMax, 50)
        xp.setWidgetProperty(self.CGLift_scrollbar,
                             xp.Property_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(
            self.CGLift_scrollbar, xp.Property_ScrollBarSliderPosition, int(world.lift_factor*10))
        xp.setWidgetDescriptor(
            self.CGLift_value, str(int(world.lift_factor*10)))
        y -= 32

        # Thrust Component
        self.CGThrust_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thrust Factor", 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGThrust_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Units", 0, self.CGWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.CGThrust_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGThrust_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CGThrust_scrollbar,
                             xp.Property_ScrollBarMin, 0)
        xp.setWidgetProperty(self.CGThrust_scrollbar,
                             xp.Property_ScrollBarMax, 100)
        xp.setWidgetProperty(self.CGThrust_scrollbar,
                             xp.Property_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(self.CGThrust_scrollbar, xp.Property_ScrollBarSliderPosition, int(
            world.thrust_factor*10))
        xp.setWidgetDescriptor(self.CGThrust_value,
                               str(world.thrust_factor*10))
        y -= 32

        # Roll Component
        self.CGRoll_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Roll Factor", 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGRoll_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Units", 0, self.CGWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.CGRoll_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGRoll_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CGRoll_scrollbar, xp.Property_ScrollBarMin, 0)
        xp.setWidgetProperty(self.CGRoll_scrollbar,
                             xp.Property_ScrollBarMax, 100)
        xp.setWidgetProperty(self.CGRoll_scrollbar,
                             xp.Property_ScrollBarPageAmount, 10)
        xp.setWidgetProperty(
            self.CGRoll_scrollbar, xp.Property_ScrollBarSliderPosition, world.roll_factor)
        xp.setWidgetDescriptor(self.CGRoll_value, str(world.roll_factor))
        y -= 32

        # Wing Size
        self.CGWing_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Wingspan    Small", 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGWing_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Large", 0, self.CGWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.CGWing_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget,  xp.WidgetClass_Caption)
        self.CGWing_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CGWing_scrollbar, xp.Property_ScrollBarMin, 1)
        xp.setWidgetProperty(self.CGWing_scrollbar,
                             xp.Property_ScrollBarMax, 100)
        xp.setWidgetProperty(self.CGWing_scrollbar,
                             xp.Property_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(self.CGWing_scrollbar,
                             xp.Property_ScrollBarSliderPosition, world.wing_size)
        xp.setWidgetDescriptor(self.CGWing_value, str(world.wing_size))
        y -= 32

        # Define checkbox for auto themals for calibration
        xp.createWidget(x+60, y-80, x+140, y-102, 1, 'Toggle Calibrate Mode ', 0,
                        self.CGWidget,  xp.WidgetClass_Caption)
        self.enableCheck1 = xp.createWidget(
            x+180, y-80, x+220, y-102, 1, '', 0, self.CGWidget, xp.WidgetClass_Button)
        xp.setWidgetProperty(self.enableCheck1,
                             xp.Property_ButtonType, xp.RadioButton)
        xp.setWidgetProperty(
            self.enableCheck1, xp.Property_ButtonBehavior, xp.ButtonBehaviorCheckBox)
        xp.setWidgetProperty(self.enableCheck1,
                             xp.Property_ButtonState,  world.CALIBRATE_MODE)
        y -= 75

        # define button
        self.CGRandom_button = xp.createWidget(x+60, y-60, x+200, y-82,
                                               1, "Roll Left", 0, self.CGWidget, xp.WidgetClass_Button)
        xp.setWidgetProperty(self.CGRandom_button,
                             xp.Property_ButtonType, xp.PushButton)

        # define button
        self.CGGenerate_button = xp.createWidget(x+320, y-60, x+440, y-82,
                                                 1, "ToBeDone", 0, self.CGWidget, xp.WidgetClass_Button)
        xp.setWidgetProperty(self.CGGenerate_button,
                             xp.Property_ButtonType, xp.PushButton)

        # --------------------------
        self.CGHandlerCB = self.CGHandler
        xp.addWidgetCallback(self.CGWidget, self.CGHandlerCB)

        # CSV MENU

    def CSVHandler(self, inMessage, inWidget, inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xp.Message_CloseButtonPushed):
            print("close button pushed")
            if (self.CSVMenuItem == 1):
                print("hide the widget")
                xp.hideWidget(self.CSVWidget)
                return 1

        # Process when a button on the widget is pressed
        if (inMessage == xp.Msg_PushButtonPressed):
            print("[button was pressed", inParam1, "]")

            # Tests the Command API, will find command
            if (inParam1 == self.CSVTGenerate_button):
                print("Generate KK7 Thermals")
                world.thermal_list = make_thermal_map_kk7(   
                     self.sim_time,                  
                     world.thermal_power, 
                     world.thermal_size)
                
                world.world_update = True
                return 1

        if (inMessage == xp.Msg_ScrollBarSliderPositionChanged):
            # Thermal Tops
            val = xp.getWidgetProperty(
                self.CSVTTops_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTTops_value, str(val))
            world.thermal_tops = int(val * world.f2m)

            # Thermal Density
            val = xp.getWidgetProperty(
                self.CSVTDensity_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTDensity_value, str(val))
            world.thermal_density = val

            # Thermal Size
            val = xp.getWidgetProperty(
                self.CSVTSize_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTSize_value, str(val))
            world.thermal_size = val

            # Thermal Power
            val = xp.getWidgetProperty(
                self.CSVTPower_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTPower_value, str(val))
            world.thermal_power = val

            # Thermal Cycle
            val = xp.getWidgetProperty(
                self.CSVTCycle_scrollbar, xp.Property_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTCycle_value, str(val))
            world.thermal_cycle = val

        return 0

    # Creates the widget with buttons for test and edit boxes for info

    def CreateCSVWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "Thermal generation from KK7 CSV"

        # create the window
        self.CSVWidget = xp.createWidget(
            x, y, x2, y2, 1, Title, 1,     0, xp.WidgetClass_MainWindow)
        xp.setWidgetProperty(
            self.CSVWidget, xp.Property_MainWindowHasCloseBoxes, 1)
        CSVWindow = xp.createWidget(
            x+50, y-50, x2-50, y2+50, 1, "",     0, self.CSVWidget, xp.WidgetClass_SubWindow)
        xp.setWidgetProperty(
            CSVWindow, xp.Property_SubWindowType, xp.SubWindowStyle_SubWindow)

        # -----------------------------
        # Thermal Tops
        self.CSVTTops_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermals Tops", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTTops_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Feet", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.CSVTTops_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTTops_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTTops_scrollbar,
                             xp.Property_ScrollBarMin, 100)
        xp.setWidgetProperty(self.CSVTTops_scrollbar,
                             xp.Property_ScrollBarMax, 20000)
        xp.setWidgetProperty(self.CSVTTops_scrollbar,
                             xp.Property_ScrollBarPageAmount, 500)
        xp.setWidgetProperty(self.CSVTTops_scrollbar, xp.Property_ScrollBarSliderPosition, int(
            world.thermal_tops*world.m2f))
        xp.setWidgetDescriptor(self.CSVTTops_value, str(
            int(world.thermal_tops*world.m2f)))
        y -= 32

        # Thermal Density
        self.CSVTDensity_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Density", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTDensity_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max # of Thermals", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.CSVTDensity_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTDensity_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTDensity_scrollbar,
                             xp.Property_ScrollBarMin, 1)
        xp.setWidgetProperty(self.CSVTDensity_scrollbar,
                             xp.Property_ScrollBarMax, 500)
        xp.setWidgetProperty(self.CSVTDensity_scrollbar,
                             xp.Property_ScrollBarPageAmount, 10)
        xp.setWidgetProperty(self.CSVTDensity_scrollbar,
                             xp.Property_ScrollBarSliderPosition, world.thermal_density)
        xp.setWidgetDescriptor(self.CSVTDensity_value,
                               str(world.thermal_density))
        y -= 32

        # Thermal Size
        self.CSVTSize_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Size", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTSize_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max Diameter m", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.CSVTSize_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTSize_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTSize_scrollbar,
                             xp.Property_ScrollBarMin, 50)
        xp.setWidgetProperty(self.CSVTSize_scrollbar,
                             xp.Property_ScrollBarMax, 1500)
        xp.setWidgetProperty(self.CSVTSize_scrollbar,
                             xp.Property_ScrollBarPageAmount, 20)
        xp.setWidgetProperty(self.CSVTSize_scrollbar,
                             xp.Property_ScrollBarSliderPosition, world.thermal_size)
        xp.setWidgetDescriptor(self.CSVTSize_value, str(world.thermal_size))
        y -= 32

        # Thermal Strength
        self.CSVTPower_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Vs", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTPower_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max m/s", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        # define scrollbar
        self.CSVTPower_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTPower_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTPower_scrollbar,
                             xp.Property_ScrollBarMin, 1)
        xp.setWidgetProperty(self.CSVTPower_scrollbar,
                             xp.Property_ScrollBarMax, 15)
        xp.setWidgetProperty(self.CSVTPower_scrollbar,
                             xp.Property_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(self.CSVTPower_scrollbar,
                             xp.Property_ScrollBarSliderPosition, world.thermal_power)
        xp.setWidgetDescriptor(self.CSVTPower_value, str(world.thermal_power))
        y -= 32

        # Thermal Cycle time
        self.CSVTCycle_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Cycle Time", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTCycle_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Minutes", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTCycle_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget,  xp.WidgetClass_Caption)
        self.CSVTCycle_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xp.WidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTCycle_scrollbar,
                             xp.Property_ScrollBarMin, 5)
        xp.setWidgetProperty(self.CSVTCycle_scrollbar,
                             xp.Property_ScrollBarMax, 90)
        xp.setWidgetProperty(self.CSVTCycle_scrollbar,
                             xp.Property_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(self.CSVTCycle_scrollbar,
                             xp.Property_ScrollBarSliderPosition, world.thermal_cycle)
        xp.setWidgetDescriptor(self.CSVTCycle_value, str(world.thermal_cycle))
        y -= 30

        # define "Generate Thermals button
        self.CSVTGenerate_button = xp.createWidget(x+320, y-60, x+440, y-82,
                                                   1, "Generate Thermals", 0, self.CSVWidget, xp.WidgetClass_Button)
        xp.setWidgetProperty(self.CSVTGenerate_button,
                             xp.Property_ButtonType, xp.PushButton)

        # --------------------------
        self.CSVHandlerCB = self.CSVHandler
        xp.addWidgetCallback(self.CSVWidget, self.CSVHandlerCB)

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
