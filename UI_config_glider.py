import world
import xp

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

        if (inParam1 == self.CGRoll_button):
            print("Glider Config: roll wing left")
            world.roll_test_pulse = 50
            return 1
        
        if (inParam1 == self.CGPitch_button):
            print("Glider Config: Pitch nose Up")
            world.pitch_test_pulse = 50
            return 1

    # Process when a scrollbar on the widget is changed
    if (inMessage == xp.Msg_ScrollBarSliderPositionChanged):
        # Lift Factor
        val = xp.getWidgetProperty(
            self.CGLift_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.CGLift_value, str(val))
        world.thrust_factor = val 

        # Thrust Factor
        val = xp.getWidgetProperty(
            self.CGThrust_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.CGThrust_value, str(val))
        world.lift_factor = val 

        # Pitch Factor
        val = xp.getWidgetProperty(
            self.CGPitch_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.CGPitch_value, str(val))
        world.pitch_factor = val

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

        # Tail Size
        val = xp.getWidgetProperty(
            self.CGTail_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.CGTail_value, str(val))
        world.tail_size = val

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
    CGLift_message0 = "Trim the glider for flight at best glide speed. ( flight model Ctrl-m )"
    CGLift_message1 = "Adjust the lift & thrust factors until vario shows 1m/s Vs"
    self.CGLift_label_a = xp.createWidget(
        x+80,  y-20, x+140, y-35, 1, CGLift_message0, 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGLift_label_b = xp.createWidget(
        x+110,  y-28, x+140, y-60, 1, CGLift_message1, 0, self.CGWidget,  xp.WidgetClass_Caption)
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
    self.CGThrust_value = xp.createWidget(
        x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGThrust_scrollbar = xp.createWidget(
        x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xp.WidgetClass_ScrollBar)
    xp.setWidgetProperty(self.CGThrust_scrollbar, xp.Property_ScrollBarMin, 0)
    xp.setWidgetProperty(self.CGThrust_scrollbar,
                            xp.Property_ScrollBarMax, 100)
    xp.setWidgetProperty(self.CGThrust_scrollbar,
                            xp.Property_ScrollBarPageAmount, 1)
    xp.setWidgetProperty(
        self.CGThrust_scrollbar, xp.Property_ScrollBarSliderPosition, int(world.thrust_factor*10))
    xp.setWidgetDescriptor(
        self.CGThrust_value, str(int(world.thrust_factor*10)))
    y -= 32

    # Roll Component
    self.CGRoll_label1 = xp.createWidget(
        x+60,  y-80, x+140, y-102, 1, "Roll Factor", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGRoll_label2 = xp.createWidget(
        x+375, y-80, x+410, y-102, 1, "Units", 0, self.CGWidget,  xp.WidgetClass_Caption)
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

    self.CGPitch_label1 = xp.createWidget(
        x+60,  y-80, x+140, y-102, 1, "Pitch Factor", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGPitch_label2 = xp.createWidget(
        x+375, y-80, x+410, y-102, 1, "Units", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGPitch_value = xp.createWidget(
        x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGPitch_scrollbar = xp.createWidget(
        x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xp.WidgetClass_ScrollBar)
    xp.setWidgetProperty(self.CGPitch_scrollbar, xp.Property_ScrollBarMin, 0)
    xp.setWidgetProperty(self.CGPitch_scrollbar,
                            xp.Property_ScrollBarMax, 100)
    xp.setWidgetProperty(self.CGPitch_scrollbar,
                            xp.Property_ScrollBarPageAmount, 10)
    xp.setWidgetProperty(self.CGPitch_scrollbar,
                            xp.Property_ScrollBarSliderPosition, world.pitch_factor)
    xp.setWidgetDescriptor(self.CGPitch_value, str(world.pitch_factor))
    y -= 32

    self.CGWing_label1 = xp.createWidget(
        x+60,  y-80, x+140, y-102, 1, "Wingspan    Small", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGWing_label2 = xp.createWidget(
        x+375, y-80, x+410, y-102, 1, "Large", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGWing_value = xp.createWidget(
        x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGWing_scrollbar = xp.createWidget(
        x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xp.WidgetClass_ScrollBar)
    xp.setWidgetProperty(self.CGWing_scrollbar, xp.Property_ScrollBarMin, 1)
    xp.setWidgetProperty(self.CGWing_scrollbar,
                            xp.Property_ScrollBarMax, 100)
    xp.setWidgetProperty(self.CGWing_scrollbar,
                            xp.Property_ScrollBarPageAmount, 10)
    xp.setWidgetProperty(self.CGWing_scrollbar,
                            xp.Property_ScrollBarSliderPosition, world.wing_size)
    xp.setWidgetDescriptor(self.CGWing_value, str(world.wing_size))
    y -= 32

    self.CGTail_label1 = xp.createWidget(
        x+60,  y-80, x+140, y-102, 1, "Tail Dist   Small", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGTail_label2 = xp.createWidget(
        x+375, y-80, x+410, y-102, 1, "Large", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGTail_value = xp.createWidget(
        x+260, y-68, x+330, y-82, 1, "  0", 0, self.CGWidget,  xp.WidgetClass_Caption)
    self.CGTail_scrollbar = xp.createWidget(
        x+170, y-80, x+370, y-102, 1, "", 0, self.CGWidget, xp.WidgetClass_ScrollBar)
    xp.setWidgetProperty(self.CGTail_scrollbar, xp.Property_ScrollBarMin, 1)
    xp.setWidgetProperty(self.CGTail_scrollbar,
                            xp.Property_ScrollBarMax, 100)
    xp.setWidgetProperty(self.CGTail_scrollbar,
                            xp.Property_ScrollBarPageAmount, 10)
    xp.setWidgetProperty(self.CGTail_scrollbar,
                            xp.Property_ScrollBarSliderPosition, world.tail_size)
    xp.setWidgetDescriptor(self.CGTail_value, str(world.tail_size))
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

    # define Roll Left button
    self.CGRoll_button = xp.createWidget(x+60, y-50, x+200, y-72,
                                            1, "Roll Left", 0, self.CGWidget, xp.WidgetClass_Button)
    xp.setWidgetProperty(self.CGRoll_button,
                            xp.Property_ButtonType, xp.PushButton)

    # define Pitch Up button
    self.CGPitch_button = xp.createWidget(x+320, y-50, x+440, y-72,
                                                1, "Pitch Up", 0, self.CGWidget, xp.WidgetClass_Button)
    xp.setWidgetProperty(self.CGPitch_button,
                            xp.Property_ButtonType, xp.PushButton)

    # --------------------------
    self.CGHandlerCB = self.CGHandler
    xp.addWidgetCallback(self.CGWidget, self.CGHandlerCB)
