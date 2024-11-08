import xp
import imgui # type: ignore
from XPPython3 import xp_imgui # type: ignore
from thermal_model import make_random_thermal_map
import world

def create_TC_Window(self):
    world.TC_WINDOW_OPEN = True
    title = 'Thermal Generator Configuration'
    if world.DEBUG > 1:
        print("Creating TC Window")
    
    l, t, r, b = xp.getScreenBoundsGlobal()
    width = 600
    height = 400
    left_offset = 110
    top_offset = 110

    world.TC_WINDOW = xp_imgui.Window(
        left=l + left_offset,
        top=t - top_offset,
        right=l + left_offset + width,
        bottom=t - (top_offset + height),
        visible=1,
        draw=self.draw_TC_Window,
        refCon=world.TC_WINDOW
    )
    world.TC_WINDOW.setTitle(title)
    return

def draw_TC_Window(self, windowID, refCon):
    if not world.TC_WINDOW_OPEN:
        return

    # Thermal Tops
    imgui.text("Thermals Tops (Meters)")
    changed, world.thermal_tops = imgui.slider_int("##ThermalTops", world.thermal_tops , 1, 10000)
    if changed:
        print("Thermal Tops", world.thermal_tops)

    imgui.text("")

    # Thermal Distance
    imgui.text("T. Separation (Meters)")
    changed, world.thermal_distance = imgui.slider_int("##ThermalDistance", world.thermal_distance, 200, 10000)
    if changed:
        print("Thermal Distance", world.thermal_distance)

    imgui.text("")

    # Thermal Refresh Time
    imgui.text("Thermals Refresh (Minutes)")
    changed, world.thermal_refresh_time = imgui.slider_int("##ThermalRefresh", world.thermal_refresh_time, 10, 200)
    if changed:
        print("Thermal Refresh Time", world.thermal_refresh_time)

    imgui.text("")

    # Thermal Density
    imgui.text("Thermal Density (# of Thermals)")
    changed, world.thermal_density = imgui.slider_int("##ThermalDensity", world.thermal_density, 10, 500)
    if changed:
        print("Thermal Density", world.thermal_density)

    imgui.text("")

    # Thermal Size
    imgui.text("Thermal Size (Max Diameter m)")
    changed, world.thermal_size = imgui.slider_int("##ThermalSize", world.thermal_size, 50, 3000)
    if changed:
        print("Thermal Size", world.thermal_size)

    imgui.text("")

    # Thermal Strength
    imgui.text("Thermal Strength (m/s)")
    changed, world.thermal_power = imgui.slider_int("##ThermalStrength", world.thermal_power, 1, 15)
    if changed:
        print("Thermal Strength", world.thermal_power)

    imgui.text("")

    # Thermal Cycle Time
    #imgui.text("Cycle Time (Minutes)")
    #changed, world.thermal_cycle = imgui.slider_int("##ThermalCycle", world.thermal_cycle, 5, 90)
    #if changed:
    #    print("Cycle Time", world.thermal_cycle)

    #imgui.text("")

    if imgui.button("Generate Thermals"):
        print("Generate Thermals button clicked")
        print("minimum separation between thermals :", world.thermal_distance)
        lat = xp.getDataf(self.PlaneLat)
        lon = xp.getDataf(self.PlaneLon)
        world.thermal_list = make_random_thermal_map(world.sim_time,
                                                            lat, lon,
                                                            world.thermal_power,
                                                            world.thermal_density,
                                                            world.thermal_size)
        world.world_update = True
        world.update_loop = 101
