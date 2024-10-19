from thermal_model import make_thermal_map_kk7
import world
import xp


def KK7Handler(self, inMessage, inWidget, inParam1, inParam2):
    # When widget close cross is clicked we only hide the widget
    if (inMessage == xp.Message_CloseButtonPushed):
        print("close button pushed")
        if (self.KK7MenuItem == 1):
            print("hide the widget")
            xp.hideWidget(self.KK7Widget)
            return 1

    # Process when a button on the widget is pressed
    if (inMessage == xp.Msg_PushButtonPressed):
        print("[button was pressed", inParam1, "]")

        # Tests the Command API, will find command
        if (inParam1 == self.KK7TGenerate_button):
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
            self.KK7TTops_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.KK7TTops_value, str(val))
        world.thermal_tops = int(val * world.f2m)

        # Thermal Size
        val = xp.getWidgetProperty(
            self.KK7TSize_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.KK7TSize_value, str(val))
        world.thermal_size = val

        # Thermal Power
        val = xp.getWidgetProperty(
            self.KK7TPower_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.KK7TPower_value, str(val))
        world.thermal_power = val

        # Thermal Cycle
        val = xp.getWidgetProperty(
            self.KK7TCycle_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.KK7TCycle_value, str(val))
        world.thermal_cycle = val

    return 0

# Creates the widget with buttons for test and edit boxes for info
# Create KK7Window
def CreateKK7Window(self, x, y, w, h):
    x2 = x + w
    y2 = y - h
    Title = "Thermal generation from KK7 CSV"

    # create the window
    self.KK7Widget = xp.createWidget(
        x, y, x2, y2, 1, Title, 1,     0, xp.WidgetClass_MainWindow)
    xp.setWidgetProperty(
        self.KK7Widget, xp.Property_MainWindowHasCloseBoxes, 1)
    KK7Window = xp.createWidget(
        x+50, y-50, x2-50, y2+50, 1, "",     0, self.KK7Widget, xp.WidgetClass_SubWindow)
    xp.setWidgetProperty(
        KK7Window, xp.Property_SubWindowType, xp.SubWindowStyle_SubWindow)

    # -----------------------------
    # Thermal Tops
    self.KK7TTops_label1 = xp.createWidget(
        x+60,  y-80, x+140, y-102, 1, "Thermals Tops", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TTops_label2 = xp.createWidget(
        x+375, y-80, x+410, y-102, 1, "Feet", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    # define scrollbar
    self.KK7TTops_value = xp.createWidget(
        x+260, y-68, x+330, y-82, 1, "  0", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TTops_scrollbar = xp.createWidget(
        x+170, y-80, x+370, y-102, 1, "", 0, self.KK7Widget, xp.WidgetClass_ScrollBar)
    xp.setWidgetProperty(self.KK7TTops_scrollbar,
                            xp.Property_ScrollBarMin, 100)
    xp.setWidgetProperty(self.KK7TTops_scrollbar,
                            xp.Property_ScrollBarMax, 20000)
    xp.setWidgetProperty(self.KK7TTops_scrollbar,
                            xp.Property_ScrollBarPageAmount, 500)
    xp.setWidgetProperty(self.KK7TTops_scrollbar, xp.Property_ScrollBarSliderPosition, int(
        world.thermal_tops*world.m2f))
    xp.setWidgetDescriptor(self.KK7TTops_value, str(
        int(world.thermal_tops*world.m2f)))
    y -= 32


    # Thermal Size
    self.KK7TSize_label1 = xp.createWidget(
        x+60,  y-80, x+140, y-102, 1, "Thermal Size", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TSize_label2 = xp.createWidget(
        x+375, y-80, x+410, y-102, 1, "Max Diameter m", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    # define scrollbar
    self.KK7TSize_value = xp.createWidget(
        x+260, y-68, x+330, y-82, 1, "  0", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TSize_scrollbar = xp.createWidget(
        x+170, y-80, x+370, y-102, 1, "", 0, self.KK7Widget, xp.WidgetClass_ScrollBar)
    xp.setWidgetProperty(self.KK7TSize_scrollbar,
                            xp.Property_ScrollBarMin, 50)
    xp.setWidgetProperty(self.KK7TSize_scrollbar,
                            xp.Property_ScrollBarMax, 1500)
    xp.setWidgetProperty(self.KK7TSize_scrollbar,
                            xp.Property_ScrollBarPageAmount, 20)
    xp.setWidgetProperty(self.KK7TSize_scrollbar,
                            xp.Property_ScrollBarSliderPosition, world.thermal_size)
    xp.setWidgetDescriptor(self.KK7TSize_value, str(world.thermal_size))
    y -= 32

    # Thermal Strength
    self.KK7TPower_label1 = xp.createWidget(
        x+60,  y-80, x+140, y-102, 1, "Thermal Vs", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TPower_label2 = xp.createWidget(
        x+375, y-80, x+410, y-102, 1, "Max m/s", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    # define scrollbar
    self.KK7TPower_value = xp.createWidget(
        x+260, y-68, x+330, y-82, 1, "  0", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TPower_scrollbar = xp.createWidget(
        x+170, y-80, x+370, y-102, 1, "", 0, self.KK7Widget, xp.WidgetClass_ScrollBar)
    xp.setWidgetProperty(self.KK7TPower_scrollbar,
                            xp.Property_ScrollBarMin, 1)
    xp.setWidgetProperty(self.KK7TPower_scrollbar,
                            xp.Property_ScrollBarMax, 15)
    xp.setWidgetProperty(self.KK7TPower_scrollbar,
                            xp.Property_ScrollBarPageAmount, 1)
    xp.setWidgetProperty(self.KK7TPower_scrollbar,
                            xp.Property_ScrollBarSliderPosition, world.thermal_power)
    xp.setWidgetDescriptor(self.KK7TPower_value, str(world.thermal_power))
    y -= 32

    # Thermal Cycle time
    self.KK7TCycle_label1 = xp.createWidget(
        x+60,  y-80, x+140, y-102, 1, "Cycle Time", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TCycle_label2 = xp.createWidget(
        x+375, y-80, x+410, y-102, 1, "Minutes", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TCycle_value = xp.createWidget(
        x+260, y-68, x+330, y-82, 1, "  0", 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.KK7TCycle_scrollbar = xp.createWidget(
        x+170, y-80, x+370, y-102, 1, "", 0, self.KK7Widget, xp.WidgetClass_ScrollBar)
    xp.setWidgetProperty(self.KK7TCycle_scrollbar,
                            xp.Property_ScrollBarMin, 5)
    xp.setWidgetProperty(self.KK7TCycle_scrollbar,
                            xp.Property_ScrollBarMax, 90)
    xp.setWidgetProperty(self.KK7TCycle_scrollbar,
                            xp.Property_ScrollBarPageAmount, 1)
    xp.setWidgetProperty(self.KK7TCycle_scrollbar,
                            xp.Property_ScrollBarSliderPosition, world.thermal_cycle)
    xp.setWidgetDescriptor(self.KK7TCycle_value, str(world.thermal_cycle))
    y -= 30

    # define "Generate Thermals button
    self.KK7TGenerate_button = xp.createWidget(x+320, y-80, x+440, y-102,
                                                1, "Generate Thermals", 0, self.KK7Widget, xp.WidgetClass_Button)
    xp.setWidgetProperty(self.KK7TGenerate_button,
                            xp.Property_ButtonType, xp.PushButton)

    kk7_message0 = "1. Download thermal hotspots from  https://thermal.kk7.ch/ "
    kk7_message1 = "2. Rename file to kk7_hotspots.csv an place in the root X-Plane folder"
    self.kk7_label_a = xp.createWidget(
        x+60,  y-160, x+450, y-175, 1, kk7_message0, 0, self.KK7Widget,  xp.WidgetClass_Caption)
    self.kk7_label_b = xp.createWidget(
        x+60,  y-176, x+450, y-195, 1, kk7_message1, 0, self.KK7Widget,  xp.WidgetClass_Caption)

    # --------------------------
    self.KK7HandlerCB = self.KK7Handler
    xp.addWidgetCallback(self.KK7Widget, self.KK7HandlerCB)
