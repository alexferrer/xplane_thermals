import world
import xp
import imgui # type: ignore
from XPPython3 import xp_imgui # type: ignore

def create_About_Window(self):
    world.ABOUT_WINDOW_OPEN = True
    title = 'About Thermal Simulator'
    if world.DEBUG > 1:
        print("Creating About Window")
    
    l, t, r, b = xp.getScreenBoundsGlobal()
    width = 400
    height = 300
    left_offset = 110
    top_offset = 110

    world.ABOUT_WINDOW = xp_imgui.Window(
        left=l + left_offset,
        top=t - top_offset,
        right=l + left_offset + width,
        bottom=t - (top_offset + height),
        visible=1,
        draw=self.draw_About_Window,
        refCon=world.ABOUT_WINDOW
    )
    world.ABOUT_WINDOW.setTitle(title)
    return

def draw_About_Window(self, windowID, refCon):
    if not world.ABOUT_WINDOW_OPEN:
        return

    imgui.text("Thermal Simulator for Python 3")
    imgui.text("Author: Alex Ferrer  @ 2014, 2022")
    imgui.text("https://github.com/alexferrer/xplane_thermals/wiki")

    imgui.text("")

    # Debug Setting
    imgui.text("Debug Setting")
    imgui.same_line()
    imgui.text("Min")
    imgui.same_line()
    changed, world.DEBUG = imgui.slider_int("##DebugSetting", world.DEBUG, 0, 10)
    imgui.same_line()
    imgui.text("Max")
    if changed:
        print("Debug Setting", world.DEBUG)
