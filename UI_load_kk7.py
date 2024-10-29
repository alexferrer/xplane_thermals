from thermal_model import make_thermal_map_kk7
import world
import xp
from XPPython3 import xp_imgui # type: ignore
import imgui  # type: ignore

def loadHotspots(self,filename):
    #open file and load the hotspots
    world.thermal_list = make_thermal_map_kk7(   
                    world.sim_time,                  
                    world.thermal_power, 
                    world.thermal_size)
            
    world.world_update = True
    print("Hotspots loaded from file: ", filename)

def retrieveCSVFiles(self):
    hotspot_files = []
    result,dir_files,tot_files = xp.getDirectoryContents(xp.getSystemPath())
    for file in dir_files:
        if file.endswith(".csv"):
            hotspot_files.append(file)    
    return hotspot_files

#---------------------- imgui stuff ----------------------------
def create_CSV_Window(self):
    world.KK7_WINDOW_OPEN = True
    title = 'Load KK7/CSV Hotspots'

    # Determine where you want the window placed. Note these
    # windows are placed relative the global screen (composite
    # of all your monitors) rather than the single 'main' screen.
    l, t, r, b = xp.getScreenBoundsGlobal()
    width =  400
    height = 200
    left_offset = 110
    top_offset = 110

    # Create the imgui Window, and save it.
    world.KK7_WINDOW = xp_imgui.Window(    left=l + left_offset,
                                    top=t - top_offset,
                                    right=l + left_offset + width,
                                    bottom=t - (top_offset + height),
                                    visible=1,
                                    draw=self.draw_CSV_Window,
                                    refCon=world.KK7_WINDOW
                                )
    world.KK7_WINDOW.setTitle(title)
    return

def draw_CSV_Window(self, windowID, refCon):
    # LABEL
    imgui.text("Select a hotspot file to load from disk")

    # COMBO
    self.hotspot_files = self.retrieveCSVFiles()
    clicked, world.KK7_current = imgui.combo("", world.KK7_current, self.hotspot_files)
    if clicked:
        print("clicked", world.KK7_current, self.hotspot_files[world.KK7_current])

    # BUTTON
    imgui.same_line()  # This will position the button to the right of the combo box
    if imgui.button("Load File"):
        self.loadHotspots(self.hotspot_files[world.KK7_current])
        imgui.open_popup("File Loaded Popup")

    if imgui.begin_popup("File Loaded Popup"):
        imgui.text("Loaded "+self.hotspot_files[world.KK7_current]+" sucessfuly")
        if imgui.button("Popup OK"):
            imgui.close_current_popup()
            world.KK7_WINDOW_OPEN = False
        imgui.end_popup()            
    return

def close_KK7_Window(self):
    world.KK7_WINDOW.delete()
