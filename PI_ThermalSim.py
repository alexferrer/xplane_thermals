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
from thermal_model import calc_thermal
from thermal_model import make_random_thermal_map
from thermal_model import make_csv_thermal_map

from draw_thermals import draw_thermals_on_screen, erase_thermals_on_screen

from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *

import random
from random import randrange
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
import xp

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
        #print("------------- we are over water")
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
        mySubMenuItem = XPLMAppendMenuItem(
            XPLMFindPluginsMenu(), "Thermal Simulator", 0, 1)
        self.MyMenuHandlerCB = self.MyMenuHandlerCallback
        self.myMenu = XPLMCreateMenu(
            "Thermals", XPLMFindPluginsMenu(), mySubMenuItem, self.MyMenuHandlerCB, 0)
        XPLMAppendMenuItem(
            self.myMenu, "Generate Random Thermals", randomThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Generate CSV Thermals", csvThermal, 1)
        XPLMAppendMenuItem(self.myMenu, "Configure Glider", configGlider, 1)
        XPLMAppendMenuItem(self.myMenu, "About", aboutThermal, 1)
        # -------------------------------------------------

        world.THERMALS_VISIBLE = False
        self.Name = "ThermalSim2"
        self.Sig = "AlexFerrer.Python.ThermalSim2"
        self.Desc = "A plugin that simulates thermals (beta)"

        """ Data refs we want to record."""
        # airplane current flight info
        self.PlaneLat = xp.findDataRef("sim/flightmodel/position/latitude")
        self.PlaneLon = xp.findDataRef("sim/flightmodel/position/longitude")
        self.PlaneElev = xp.findDataRef("sim/flightmodel/position/elevation")
        self.PlaneHdg = xp.findDataRef(
            "sim/flightmodel/position/psi")  # plane heading
        self.PlaneRol = xp.findDataRef(
            "sim/flightmodel/position/phi")  # plane roll

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
        world.probe = xp.createProbe(xplm_ProbeY)
        world.terrain_is_water = xplane_terrain_is_water

        # variables to inject energy to the plane
        self.lift = EasyDref('sim/flightmodel/forces/fnrml_plug_acf', 'float')
        self.roll = EasyDref(
            'sim/flightmodel/forces/L_plug_acf', 'float')  # wing roll
        # although lift should be enough, some energy has to go as thrust, or the plane
        # might float in the air without moving!
        self.thrust = EasyDref(
            'sim/flightmodel/forces/faxil_plug_acf', 'float')

        # Drawing update flag
        world.world_update = True

        # image to mark thermals
        self.ObjectPath = "lib/dynamic/balloon.obj"

        """
        Register our callback for once a second.  Positive intervals
        are in seconds, negative are the negative of sim frames.  Zero
        registers but does not schedule a callback for time.
        """
        xp.registerFlightLoopCallback(self.FlightLoopCallback, 1.0, 0)

        return self.Name, self.Sig, self.Desc

    def XPluginStop(self):    # Unregister the callbacks
        xp.unregisterFlightLoopCallback(self.FlightLoopCallback, 0)
        #XPLMUnregisterDrawCallback(self.DrawObjectCB, xplm_Phase_Objects, 0, 0)
        # deprecated...    https://developer.x-plane.com/sdk/XPLMDrawingPhase/#xplm_Phase_Objects

        XPLMDestroyMenu(self, self.myMenu)
        # for probe suff
        xp.destroyProbe(world.probe)
        # debug
        xp.destroyWindow(self.WindowId)

    def XPluginEnable(self):
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        pass

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        # the actual callback, runs once every x period as defined

        # is the sim paused? , then skip
        runtime = xp.getDataf(self.runningTime)
        if self.sim_time == runtime:
            print("Pause - ", end='')
            return 1
        self.sim_time = runtime

        # instantiate the actual callbacks.

        lat = xp.getDataf(self.PlaneLat)
        lon = xp.getDataf(self.PlaneLon)
        elevation = xp.getDataf(self.PlaneElev)
        heading = xp.getDataf(self.PlaneHdg)
        roll_angle = xp.getDataf(self.PlaneRol)
        wind_speed = round(xp.getDataf(self.WindSpeed) *
                           0.5144, 2)      # Knots to m/s
        # Degrees to radians
        wind_dir = round(math.radians(xp.getDataf(self.WindDir)), 4)

        # sun pitch afects thermal power , noon in summer is the best..
        sun_pitch = xp.getDataf(self.SunPitch)  # Degrees
        sun_factor = (sun_pitch + 10)/100
        if sun_pitch < 0:
            sun_factor = 0

        # keep up with wind changes
        if [wind_speed, wind_dir] != [world.wind_speed, world.wind_dir]:
            [world.wind_speed, world.wind_dir] = [wind_speed, wind_dir]
            world.world_update = True
            #print( "wind changed",wind_speed,world.wind_speed,wind_dir,world.wind_dir)

        # Get the lift value of the current position from the world thermal map
        lift_val, roll_val = calc_thermal(
            lat, lon, elevation, heading, roll_angle)

        # apply sun elevation as a % factor to thermal power
        # average lift depends on sun angle over the earth.
        lift_val = lift_val * sun_factor

        # ----------------------------- for fine tuning!!! -----------------------
        # lift_val = 500
        # roll_val = 0
        # ------------------------------------------------------------------------

        # apply the force to the airplanes lift.value dataref
        lval = lift_val * world.lift_factor + self.lift.value
        self.lift.value = lval

        # although extra lift is what should be happening...
        # adding a bit of thrust works much better! -150 = 1m/s
        # apply a max thurst to a factor of 500fpm
        if lift_val > 500:
            lift_val = 500

        tval = self.thrust.value
        self.thrust.value = (- world.thrust_factor) * lift_val + tval

        # apply a roll to the plane
        rval = roll_val * world.roll_factor + self.roll.value
        self.roll.value = rval

        # Check if it is time to referesh the thermal map
        if (self.sim_time - world.thermal_map_start_time) > (world.thermal_refresh_time * 60):
            lat = xp.getDataf(self.PlaneLat)
            lon = xp.getDataf(self.PlaneLon)
            world.thermal_dict = make_random_thermal_map(self.sim_time,
                                                         lat, lon,
                                                         world.thermal_power,
                                                         world.thermal_density,
                                                         world.thermal_size)

            world.world_update = True

        # if anything has changed updte the screen drawings
        if world.world_update:
            erase_thermals_on_screen()  # clean screen of old thermals
            draw_thermals_on_screen(xp.getDataf(self.PlaneLat),
                                    xp.getDataf(self.PlaneLon)
                                    )

        # set the next callback time in +n for # of seconds and -n for # of Frames
        return .01  # works good on my (pretty fast) machine..

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
        if (inMessage == xpMessage_CloseButtonPushed):
            print("close button pushed")
            if (self.TCMenuItem == 1):
                print("hide the widget")
                xp.hideWidget(self.TCWidget)
                return 1

        # Process when a button on the widget is pressed
        if (inMessage == xpMsg_PushButtonPressed):
            print("[button was pressed", inParam1, "]")

            # Tests the Command API, will find command
            if (inParam1 == self.TGenerate_button):
                print("Generate")
                print("minimum separation between thermals ")
                print(world.thermal_distance)
                lat = xp.getDataf(self.PlaneLat)
                lon = xp.getDataf(self.PlaneLon)
                # world.cloud_streets = xp.getWidgetProperty(self.enableCheck, xpProperty_ButtonState, None)
                # lat,lon,stregth,count
                world.thermal_dict = make_random_thermal_map(self.sim_time,
                                                             lat, lon,
                                                             world.thermal_power,
                                                             world.thermal_density,
                                                             world.thermal_size)
                world.world_update = True
                return 1

        if (inMessage == xpMsg_ButtonStateChanged):
            #print("********************* toggle thermal column visibility *************")
            world.THERMALS_VISIBLE = xp.getWidgetProperty(
                self.enableCheck, xpProperty_ButtonState, None)
            world.world_update = True

        if (inMessage == xpMsg_ScrollBarSliderPositionChanged):
            # Thermal Tops
            val = xp.getWidgetProperty(
                self.TTops_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TTops_value, str(val))
            world.thermal_tops = int(val * world.f2m)

            # Thermal Density
            val = xp.getWidgetProperty(
                self.TDensity_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TDensity_value, str(val))
            world.thermal_density = val

            # Minimum Distance Between  Thermals
            val = xp.getWidgetProperty(
                self.TDistance_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TDistance_value, str(val))
            world.thermal_distance = val

            # Thermals refresh time
            val = xp.getWidgetProperty(
                self.TRefresh_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TRefresh_value, str(val))
            world.thermal_refresh_time = val

            # Thermal Size
            val = xp.getWidgetProperty(
                self.TSize_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TSize_value, str(val))
            world.thermal_size = val

            # Thermal Power
            val = xp.getWidgetProperty(
                self.TPower_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.TPower_value, str(val))
            world.thermal_power = val

            # Thermal Cycle
            val = xp.getWidgetProperty(
                self.TCycle_scrollbar, xpProperty_ScrollBarSliderPosition, None)
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
            x, y, x2, y2, 1, Title, 1,     0, xpWidgetClass_MainWindow)
        xp.setWidgetProperty(
            self.TCWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        TCWindow = xp.createWidget(
            x+50, y-50, x2-50, y2+50, 1, "",     0, self.TCWidget, xpWidgetClass_SubWindow)
        xp.setWidgetProperty(TCWindow, xpProperty_SubWindowType,
                             xpSubWindowStyle_SubWindow)

        # -----------------------------
        # Thermal Tops
        self.TTops_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermals Tops", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TTops_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Feet", 0, self.TCWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.TTops_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TTops_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TTops_scrollbar,
                             xpProperty_ScrollBarMin, 100)
        xp.setWidgetProperty(self.TTops_scrollbar,
                             xpProperty_ScrollBarMax, 20000)
        xp.setWidgetProperty(self.TTops_scrollbar,
                             xpProperty_ScrollBarPageAmount, 500)
        xp.setWidgetProperty(self.TTops_scrollbar, xpProperty_ScrollBarSliderPosition, int(
            world.thermal_tops*world.m2f))
        xp.setWidgetDescriptor(self.TTops_value, str(
            int(world.thermal_tops*world.m2f)))
        y -= 32

        # Thermal Distance
        self.TDistance_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermals Separation", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDistance_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Meters", 0, self.TCWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.TDistance_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDistance_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TDistance_scrollbar,
                             xpProperty_ScrollBarMin, 100)
        xp.setWidgetProperty(self.TDistance_scrollbar,
                             xpProperty_ScrollBarMax, 2000)
        xp.setWidgetProperty(self.TDistance_scrollbar,
                             xpProperty_ScrollBarPageAmount, 100)
        xp.setWidgetProperty(self.TDistance_scrollbar, xpProperty_ScrollBarSliderPosition, int(
            world.thermal_distance))
        xp.setWidgetDescriptor(self.TDistance_value,
                               str(int(world.thermal_distance)))
        y -= 32

        # Thermal map Refresh time
        self.TRefresh_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermals Refresh", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TRefresh_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Minutes", 0, self.TCWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.TRefresh_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TRefresh_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TRefresh_scrollbar,
                             xpProperty_ScrollBarMin, 10)
        xp.setWidgetProperty(self.TRefresh_scrollbar,
                             xpProperty_ScrollBarMax, 200)
        xp.setWidgetProperty(self.TRefresh_scrollbar,
                             xpProperty_ScrollBarPageAmount, 20)
        xp.setWidgetProperty(self.TRefresh_scrollbar, xpProperty_ScrollBarSliderPosition, int(
            world.thermal_refresh_time))
        xp.setWidgetDescriptor(self.TRefresh_value, str(
            int(world.thermal_refresh_time)))
        y -= 32

        # Thermal Density
        self.TDensity_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Density", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDensity_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "# of Thermals", 0, self.TCWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.TDensity_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TDensity_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TDensity_scrollbar,
                             xpProperty_ScrollBarMin, 10)
        xp.setWidgetProperty(self.TDensity_scrollbar,
                             xpProperty_ScrollBarMax, 500)
        xp.setWidgetProperty(self.TDensity_scrollbar,
                             xpProperty_ScrollBarPageAmount, 10)
        xp.setWidgetProperty(self.TDensity_scrollbar,
                             xpProperty_ScrollBarSliderPosition, world.thermal_density)
        xp.setWidgetDescriptor(self.TDensity_value, str(world.thermal_density))
        y -= 32

        # Thermal Size
        self.TSize_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Size", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TSize_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max Diameter m", 0, self.TCWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.TSize_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TSize_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TSize_scrollbar, xpProperty_ScrollBarMin, 50)
        xp.setWidgetProperty(self.TSize_scrollbar,
                             xpProperty_ScrollBarMax, 1500)
        xp.setWidgetProperty(self.TSize_scrollbar,
                             xpProperty_ScrollBarPageAmount, 20)
        xp.setWidgetProperty(
            self.TSize_scrollbar, xpProperty_ScrollBarSliderPosition, world.thermal_size)
        xp.setWidgetDescriptor(self.TSize_value, str(world.thermal_size))
        y -= 32

        # Thermal Strength
        self.TPower_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Power", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TPower_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max fpm", 0, self.TCWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.TPower_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TPower_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TPower_scrollbar,
                             xpProperty_ScrollBarMin, 250)
        xp.setWidgetProperty(self.TPower_scrollbar,
                             xpProperty_ScrollBarMax, 3500)
        xp.setWidgetProperty(self.TPower_scrollbar,
                             xpProperty_ScrollBarPageAmount, 10)
        xp.setWidgetProperty(
            self.TPower_scrollbar, xpProperty_ScrollBarSliderPosition, world.thermal_power)
        xp.setWidgetDescriptor(self.TPower_value, str(world.thermal_power))
        y -= 32

        # Thermal Cycle time
        self.TCycle_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Cycle Time", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TCycle_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Minutes", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TCycle_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.TCWidget, xpWidgetClass_Caption)
        self.TCycle_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.TCWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.TCycle_scrollbar, xpProperty_ScrollBarMin, 5)
        xp.setWidgetProperty(self.TCycle_scrollbar,
                             xpProperty_ScrollBarMax, 90)
        xp.setWidgetProperty(self.TCycle_scrollbar,
                             xpProperty_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(
            self.TCycle_scrollbar, xpProperty_ScrollBarSliderPosition, world.thermal_cycle)
        xp.setWidgetDescriptor(self.TCycle_value, str(world.thermal_cycle))
        y -= 30

        # Define checkbox for thermal column visibility
        xp.createWidget(x+60, y-80, x+140, y-102, 1, 'Thermals visible (cheat)',
                        0, self.TCWidget, xpWidgetClass_Caption)
        self.enableCheck = xp.createWidget(
            x+220, y-80, x+260, y-102, 1, '', 0, self.TCWidget, xpWidgetClass_Button)
        xp.setWidgetProperty(
            self.enableCheck, xpProperty_ButtonType, xpRadioButton)
        xp.setWidgetProperty(
            self.enableCheck, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        xp.setWidgetProperty(
            self.enableCheck, xpProperty_ButtonState, world.THERMALS_VISIBLE)
        y -= 75

        # define button
        self.TGenerate_button = xp.createWidget(x+320, y-60, x+440, y-82,
                                                1, "Generate Thermals", 0, self.TCWidget, xpWidgetClass_Button)
        xp.setWidgetProperty(self.TGenerate_button,
                             xpProperty_ButtonType, xpPushButton)

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
            x, y, x2, y2, 1, Title, 1,     0, xpWidgetClass_MainWindow)
        xp.setWidgetProperty(
            self.AboutWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        AboutWindow = xp.createWidget(
            x+50, y-50, x2-50, y2+50, 1, "",     0, self.AboutWidget, xpWidgetClass_SubWindow)
        xp.setWidgetProperty(
            AboutWindow, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

        text1 = "Thermal Simulator for Python 3"
        self.About_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, text1, 0, self.AboutWidget, xpWidgetClass_Caption)
        y -= 35

        text2 = "Author: Alex Ferrer  @ 2014, 2022"
        self.About_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, text2, 0, self.AboutWidget, xpWidgetClass_Caption)
        y -= 35

        text3 = " https://github.com/alexferrer/xplane_thermals/wiki"
        self.About_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, text3, 0, self.AboutWidget, xpWidgetClass_Caption)

        self.AboutHandlerCB = self.AboutHandler
        xp.addWidgetCallback(self.AboutWidget, self.AboutHandlerCB)
     # ----

    def AboutHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xpMessage_CloseButtonPushed):
            print("about close button pushed")
            if (self.AboutMenuItem == 1):
                print("hide the widget")
                xp.hideWidget(self.AboutWidget)
                return 1
        return 0
# ----------------------------------------- new...

    def CGHandler(self, inMessage, inWidget,       inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xpMessage_CloseButtonPushed):
            print("close button pushed")
            if (self.CGMenuItem == 1):
                print("hide the widget")
                xp.hideWidget(self.CGWidget)
                return 1

        # Process when a button on the widget is pressed
        if (inMessage == xpMsg_PushButtonPressed):
            print("[button was pressed", inParam1, "]")

            # Tests the Command API, will find command
            if (inParam1 == self.CGGenerate_button):
                print("Generate")
                return 1

            if (inParam1 == self.CGRandom_button):
                print("Set thermal config randomly")
                return 1

        if (inMessage == xpMsg_ScrollBarSliderPositionChanged):
            # Lift Factor
            val = xp.getWidgetProperty(
                self.CGLift_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CGLift_value, str(val))
            world.lift_factor = val * .1

            # Thrust Factor
            val = xp.getWidgetProperty(
                self.CGThrust_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CGThrust_value, str(val))
            world.thrust_factor = val * .1

            # Roll factor
            val = xp.getWidgetProperty(
                self.CGRoll_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CGRoll_value, str(val))
            world.roll_factor = val * .1

            # Wing Size
            val = xp.getWidgetProperty(
                self.CGWing_scrollbar, xpProperty_ScrollBarSliderPosition, None)
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
            x, y, x2, y2, 1, Title, 1,     0, xpWidgetClass_MainWindow)
        xp.setWidgetProperty(
            self.CGWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        CGWindow = xp.createWidget(
            x+50, y-50, x2-50, y2+50, 1, "",     0, self.CGWidget, xpWidgetClass_SubWindow)
        xp.setWidgetProperty(CGWindow, xpProperty_SubWindowType,
                             xpSubWindowStyle_SubWindow)

        # -----------------------------
        # Lift Component
        self.CGLift_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Lift Factor", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGLift_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Units", 0, self.CGWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.CGLift_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGLift_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CGLift_scrollbar, xpProperty_ScrollBarMin, 0)
        xp.setWidgetProperty(self.CGLift_scrollbar,
                             xpProperty_ScrollBarMax, 100)
        xp.setWidgetProperty(self.CGLift_scrollbar,
                             xpProperty_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(
            self.CGLift_scrollbar, xpProperty_ScrollBarSliderPosition, int(world.lift_factor*10))
        xp.setWidgetDescriptor(
            self.CGLift_value, str(int(world.lift_factor*10)))
        y -= 32

        # Thrust Component
        self.CGThrust_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thrust Factor", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGThrust_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Units", 0, self.CGWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.CGThrust_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGThrust_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CGThrust_scrollbar,
                             xpProperty_ScrollBarMin, 0)
        xp.setWidgetProperty(self.CGThrust_scrollbar,
                             xpProperty_ScrollBarMax, 100)
        xp.setWidgetProperty(self.CGThrust_scrollbar,
                             xpProperty_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(self.CGThrust_scrollbar, xpProperty_ScrollBarSliderPosition, int(
            world.thrust_factor*10))
        xp.setWidgetDescriptor(self.CGThrust_value,
                               str(world.thrust_factor*10))
        y -= 32

        # Roll Component
        self.CGRoll_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Roll Factor", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGRoll_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Units", 0, self.CGWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.CGRoll_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGRoll_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CGRoll_scrollbar, xpProperty_ScrollBarMin, 0)
        xp.setWidgetProperty(self.CGRoll_scrollbar,
                             xpProperty_ScrollBarMax, 800)
        xp.setWidgetProperty(self.CGRoll_scrollbar,
                             xpProperty_ScrollBarPageAmount, 10)
        xp.setWidgetProperty(
            self.CGRoll_scrollbar, xpProperty_ScrollBarSliderPosition, world.roll_factor)
        xp.setWidgetDescriptor(self.CGRoll_value, str(world.roll_factor))
        y -= 32

        # Wing Size
        self.CGWing_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Wing Size", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGWing_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "meters", 0, self.CGWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.CGWing_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget, xpWidgetClass_Caption)
        self.CGWing_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CGWing_scrollbar, xpProperty_ScrollBarMin, 1)
        xp.setWidgetProperty(self.CGWing_scrollbar,
                             xpProperty_ScrollBarMax, 30)
        xp.setWidgetProperty(self.CGWing_scrollbar,
                             xpProperty_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(self.CGWing_scrollbar,
                             xpProperty_ScrollBarSliderPosition, world.wing_size)
        xp.setWidgetDescriptor(self.CGWing_value, str(world.wing_size))
        y -= 32

        # Define checkbox for thermal visibility
        xp.createWidget(x+60, y-80, x+140, y-102, 1, 'xx3', 0,
                        self.CGWidget, xpWidgetClass_Caption)
        self.enableCheck1 = xp.createWidget(
            x+180, y-80, x+220, y-102, 1, '', 0, self.CGWidget, xpWidgetClass_Button)
        xp.setWidgetProperty(self.enableCheck1,
                             xpProperty_ButtonType, xpRadioButton)
        xp.setWidgetProperty(
            self.enableCheck1, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
        xp.setWidgetProperty(self.enableCheck1,
                             xpProperty_ButtonState, world.THERMALS_VISIBLE)
        y -= 75

        # define button
        self.CGRandom_button = xp.createWidget(x+60, y-60, x+200, y-82,
                                               1, "xx2", 0, self.CGWidget, xpWidgetClass_Button)
        xp.setWidgetProperty(self.CGRandom_button,
                             xpProperty_ButtonType, xpPushButton)

        # define button
        self.CGGenerate_button = xp.createWidget(x+320, y-60, x+440, y-82,
                                                 1, "xxx1", 0, self.CGWidget, xpWidgetClass_Button)
        xp.setWidgetProperty(self.CGGenerate_button,
                             xpProperty_ButtonType, xpPushButton)

        # --------------------------
        self.CGHandlerCB = self.CGHandler
        xp.addWidgetCallback(self.CGWidget, self.CGHandlerCB)

        # CSV MENU

    def CSVHandler(self, inMessage, inWidget, inParam1, inParam2):
        # When widget close cross is clicked we only hide the widget
        if (inMessage == xpMessage_CloseButtonPushed):
            print("close button pushed")
            if (self.CSVMenuItem == 1):
                print("hide the widget")
                xp.hideWidget(self.CSVWidget)
                return 1

        # Process when a button on the widget is pressed
        if (inMessage == xpMsg_PushButtonPressed):
            print("[button was pressed", inParam1, "]")

            # Tests the Command API, will find command
            if (inParam1 == self.CSVTGenerate_button):
                print("Generate")
                lat = xp.getDataf(self.PlaneLat)
                lon = xp.getDataf(self.PlaneLon)
                world.thermal_dict = make_csv_thermal_map(
                    lat, lon, world.thermal_power, world.thermal_density, world.thermal_size)
                world.world_update = True
                return 1

        if (inMessage == xpMsg_ScrollBarSliderPositionChanged):
            # Thermal Tops
            val = xp.getWidgetProperty(
                self.CSVTTops_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTTops_value, str(val))
            world.thermal_tops = int(val * world.f2m)

            # Thermal Density
            val = xp.getWidgetProperty(
                self.CSVTDensity_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTDensity_value, str(val))
            world.thermal_density = val

            # Thermal Size
            val = xp.getWidgetProperty(
                self.CSVTSize_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTSize_value, str(val))
            world.thermal_size = val

            # Thermal Power
            val = xp.getWidgetProperty(
                self.CSVTPower_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTPower_value, str(val))
            world.thermal_power = val

            # Thermal Cycle
            val = xp.getWidgetProperty(
                self.CSVTCycle_scrollbar, xpProperty_ScrollBarSliderPosition, None)
            xp.setWidgetDescriptor(self.CSVTCycle_value, str(val))
            world.thermal_cycle = val

        return 0

    # Creates the widget with buttons for test and edit boxes for info

    def CreateCSVWindow(self, x, y, w, h):
        x2 = x + w
        y2 = y - h
        Title = "Thermal generation from CSV"

        # create the window
        self.CSVWidget = xp.createWidget(
            x, y, x2, y2, 1, Title, 1,     0, xpWidgetClass_MainWindow)
        xp.setWidgetProperty(
            self.CSVWidget, xpProperty_MainWindowHasCloseBoxes, 1)
        CSVWindow = xp.createWidget(
            x+50, y-50, x2-50, y2+50, 1, "",     0, self.CSVWidget, xpWidgetClass_SubWindow)
        xp.setWidgetProperty(
            CSVWindow, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

        # -----------------------------
        # Thermal Tops
        self.CSVTTops_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermals Tops", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTTops_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Feet", 0, self.CSVWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.CSVTTops_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTTops_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTTops_scrollbar,
                             xpProperty_ScrollBarMin, 100)
        xp.setWidgetProperty(self.CSVTTops_scrollbar,
                             xpProperty_ScrollBarMax, 20000)
        xp.setWidgetProperty(self.CSVTTops_scrollbar,
                             xpProperty_ScrollBarPageAmount, 500)
        xp.setWidgetProperty(self.CSVTTops_scrollbar, xpProperty_ScrollBarSliderPosition, int(
            world.thermal_tops*world.m2f))
        xp.setWidgetDescriptor(self.CSVTTops_value, str(
            int(world.thermal_tops*world.m2f)))
        y -= 32

        # Thermal Density
        self.CSVTDensity_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Density", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTDensity_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max # of Thermals", 0, self.CSVWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.CSVTDensity_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTDensity_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTDensity_scrollbar,
                             xpProperty_ScrollBarMin, 1)
        xp.setWidgetProperty(self.CSVTDensity_scrollbar,
                             xpProperty_ScrollBarMax, 500)
        xp.setWidgetProperty(self.CSVTDensity_scrollbar,
                             xpProperty_ScrollBarPageAmount, 10)
        xp.setWidgetProperty(self.CSVTDensity_scrollbar,
                             xpProperty_ScrollBarSliderPosition, world.thermal_density)
        xp.setWidgetDescriptor(self.CSVTDensity_value,
                               str(world.thermal_density))
        y -= 32

        # Thermal Size
        self.CSVTSize_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Size", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTSize_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max Diameter m", 0, self.CSVWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.CSVTSize_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTSize_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTSize_scrollbar,
                             xpProperty_ScrollBarMin, 50)
        xp.setWidgetProperty(self.CSVTSize_scrollbar,
                             xpProperty_ScrollBarMax, 1500)
        xp.setWidgetProperty(self.CSVTSize_scrollbar,
                             xpProperty_ScrollBarPageAmount, 20)
        xp.setWidgetProperty(self.CSVTSize_scrollbar,
                             xpProperty_ScrollBarSliderPosition, world.thermal_size)
        xp.setWidgetDescriptor(self.CSVTSize_value, str(world.thermal_size))
        y -= 32

        # Thermal Strength
        self.CSVTPower_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Thermal Power", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTPower_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Max fpm", 0, self.CSVWidget, xpWidgetClass_Caption)
        # define scrollbar
        self.CSVTPower_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTPower_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTPower_scrollbar,
                             xpProperty_ScrollBarMin, 250)
        xp.setWidgetProperty(self.CSVTPower_scrollbar,
                             xpProperty_ScrollBarMax, 3500)
        xp.setWidgetProperty(self.CSVTPower_scrollbar,
                             xpProperty_ScrollBarPageAmount, 10)
        xp.setWidgetProperty(self.CSVTPower_scrollbar,
                             xpProperty_ScrollBarSliderPosition, world.thermal_power)
        xp.setWidgetDescriptor(self.CSVTPower_value, str(world.thermal_power))
        y -= 32

        # Thermal Cycle time
        self.CSVTCycle_label1 = xp.createWidget(
            x+60,  y-80, x+140, y-102, 1, "Cycle Time", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTCycle_label2 = xp.createWidget(
            x+375, y-80, x+410, y-102, 1, "Minutes", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTCycle_value = xp.createWidget(
            x+260, y-68, x+330, y-82, 1, "  0", 0, self.CSVWidget, xpWidgetClass_Caption)
        self.CSVTCycle_scrollbar = xp.createWidget(
            x+170, y-80, x+370, y-102, 1, "", 0, self.CSVWidget, xpWidgetClass_ScrollBar)
        xp.setWidgetProperty(self.CSVTCycle_scrollbar,
                             xpProperty_ScrollBarMin, 5)
        xp.setWidgetProperty(self.CSVTCycle_scrollbar,
                             xpProperty_ScrollBarMax, 90)
        xp.setWidgetProperty(self.CSVTCycle_scrollbar,
                             xpProperty_ScrollBarPageAmount, 1)
        xp.setWidgetProperty(self.CSVTCycle_scrollbar,
                             xpProperty_ScrollBarSliderPosition, world.thermal_cycle)
        xp.setWidgetDescriptor(self.CSVTCycle_value, str(world.thermal_cycle))
        y -= 30

        # define button
        self.CSVTGenerate_button = xp.createWidget(x+320, y-60, x+440, y-82,
                                                   1, "Generate Thermals", 0, self.CSVWidget, xpWidgetClass_Button)
        xp.setWidgetProperty(self.CSVTGenerate_button,
                             xpProperty_ButtonType, xpPushButton)

        # --------------------------
        self.CSVHandlerCB = self.CSVHandler
        xp.addWidgetCallback(self.CSVWidget, self.CSVHandlerCB)

    # ------- after this debug
