import xp
import imgui # type: ignore
from XPPython3 import xp_imgui # type: ignore
import world

def create_Stats_Window(self):
    world.STATS_WINDOW_OPEN = True
    title = 'Thermal Stats'
    if world.DEBUG > 1: print("Creating Stats Window")
    
    l, t, r, b = xp.getScreenBoundsGlobal()
    width = 450
    height = 300
    left_offset = 110
    top_offset = 110

    world.STATS_WINDOW = xp_imgui.Window(
        left=l + left_offset,
        top=t - top_offset,
        right=l + left_offset + width,
        bottom=t - (top_offset + height),
        visible=1,
        draw=self.draw_Stats_Window,
        refCon=world.STATS_WINDOW
    )
    world.STATS_WINDOW.setTitle(title)
    return

def draw_Stats_Window(self, windowID, refCon):
    if not world.STATS_WINDOW_OPEN:
        return

    if world.thermal_radius > world.distance_from_center:
        imgui.text_colored("IN THERMAL", 0.0, 1.0, 0.0)
    else:
        imgui.text_colored("OFF THERMAL", 1.0, 0.0, 0.0)


    imgui.columns(2)
    imgui.text(f"Distance: {int(world.distance_from_center)}  m")
    imgui.text(f"T Radius: {int(world.thermal_radius)} m")
    imgui.next_column()
    imgui.text(f"T Strength: {round(world.thermal_strength, 2)} m/s")
    imgui.text(f"Lfactor: {round(world.lift_factor, 2)} X")
    imgui.columns(1)
    imgui.text(f"Rfactor: {round(world.roll_factor, 2)} X")
    imgui.text(f"Pfactor: {round(world.pitch_factor, 2)} X")

    if world.thermal_radius > world.distance_from_center:
        imgui.columns(2)
        imgui.text(f"T Lift: {round(world.tot_lift_force, 2)} m/s")
        imgui.text(f"T Roll: {round(world.tot_roll_force, 2)} N")
        imgui.next_column()
        imgui.text(f"% {round(world.cal_lift_force, 2)} m/s")
        imgui.text(f"% {round(world.applied_roll_force, 2)} N")
        imgui.columns(1)

        imgui.text(f"Thrust: {round(world.tot_thrust_force, 2)} N")
        imgui.text(f"Applied: {round(world.applied_lift_force, 2)} N")

    imgui.text(f"[{world.message}]")
    imgui.text_colored(f"[{world.message1}]", 0.0, 1.0, 0.0)
    imgui.text(f"[{world.message2}]")

   