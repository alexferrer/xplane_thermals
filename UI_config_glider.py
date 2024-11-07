import world
import xp
import imgui #type: ignore
from XPPython3 import xp_imgui # type: ignore

def create_CG_Window(self):
    world.CG_WINDOW_OPEN = True
    title = 'Configure Glider'
    if world.DEBUG > 1:
        print("Creating CG Window")
    
    l, t, r, b = xp.getScreenBoundsGlobal()
    width = 600
    height = 250
    left_offset = 110
    top_offset = 110

    world.CG_WINDOW = xp_imgui.Window(
        left=l + left_offset,
        top=t - top_offset,
        right=l + left_offset + width,
        bottom=t - (top_offset + height),
        visible=1,
        draw=self.draw_CG_Window,
        refCon=world.CG_WINDOW
    )
    world.CG_WINDOW.setTitle(title)
    return

def draw_CG_Window(self, windowID, refCon):
    if not world.CG_WINDOW_OPEN:
        world.CALIBRATE_MODE = False
        return
    
    imgui.text("Trim the glider for flight at best glide speed. ( flight model Ctrl-m )")
    imgui.text("Adjust the lift & thrust factors until vario shows 1m/s Vs.")
    imgui.text("")

    # Scrollbars

    changed, world.calibrate_factor_ms = imgui.slider_int("Calibrate Vs m/s", world.calibrate_factor_ms, 0, 10)
    if changed:
        print("Calibrate thermal m/s", world.calibrate_factor_ms)

    imgui.text("")

    changed, world.lift_factor = imgui.slider_int("Lift Factor", world.lift_factor, 0, 100)
    if changed:
        print("Lift Factor", world.lift_factor)

    changed, world.thrust_factor = imgui.slider_int("Thrust Factor", world.thrust_factor, 0, 100)
    if changed:
        print("Thrust Factor", world.thrust_factor)

    changed, world.pitch_factor = imgui.slider_int("Pitch Factor", world.pitch_factor, -50, 50)
    if changed:
        print("Pitch Factor", world.pitch_factor)

    changed, world.roll_factor = imgui.slider_int("Roll Factor", world.roll_factor, -50, 50)
    if changed:
        print("Roll Factor", world.roll_factor)
    
    
    imgui.separator()
    # Radiobutton
    changed, world.CALIBRATE_MODE = imgui.checkbox("Calibrate Mode", world.CALIBRATE_MODE)
    if changed:
        print("CALIBRATE_MODE", world.CALIBRATE_MODE)


    # Buttons
    imgui.columns(2, 'buttons')
    
    if imgui.button("Roll Wing Left"):
        print("Glider Config: roll wing left")
        world.roll_test_pulse = 50
    
    imgui.next_column()
    
    if imgui.button("Pitch Nose Up"):
        print("Glider Config: Pitch nose Up")
        world.pitch_test_pulse = 50
    
    imgui.columns(1)

    return