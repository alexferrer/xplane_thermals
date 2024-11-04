from thermal_model import make_random_thermal_map
import xp
import world

def TCHandler(self, inMessage, inWidget, inParam1, inParam2):
    if (inMessage == xp.Message_CloseButtonPushed):
        if (self.TCMenuItem == 1):
            xp.hideWidget(self.TCWidget)
            return 1

    if (inMessage == xp.Msg_PushButtonPressed):

        # Tests the Command API, will find command
        if (inParam1 == self.TGenerate_button):
            print("Menu: Generate Thermals")
            print("minimum separation between thermals :", world.thermal_distance)
            lat = xp.getDataf(self.PlaneLat)
            lon = xp.getDataf(self.PlaneLon)
            #world.cloud_streets = xp.getWidgetProperty(self.enableCheck, xp.Property_ButtonState, None)
            #print("enable cloud streets", world.cloud_streets)
            # lat,lon,stregth,count
            world.thermal_list = make_random_thermal_map(world.sim_time,
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


