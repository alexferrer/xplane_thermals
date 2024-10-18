import xp
import world
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
    if (inMessage == xp.Message_CloseButtonPushed ):
        if (self.AboutMenuItem == 1):
            xp.hideWidget(self.AboutWidget)
            return 1
    if (inMessage == xp.Msg_ScrollBarSliderPositionChanged):
        val = xp.getWidgetProperty(
            self.DBug_scrollbar, xp.Property_ScrollBarSliderPosition, None)
        xp.setWidgetDescriptor(self.DBug_value, str(val))
        world.DEBUG = int(val)
        print("DEBUG LEVEL ", world.DEBUG)

    return 0
# ----------------------------------------- new...

