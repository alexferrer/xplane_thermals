''' 
  File: world.py
  Auth: Alex Ferrer @ 2014
  Central file to store all globally used variables.
  
  It is ugly to have globals but we depend on Xplane for lots of them
  so I rather read them once and store them here for all to use.
 
  * We store variables in their ready to use units format, (usually metric)
'''

''' Our thermal map is a mesh representing 1x1 degree, so it use only 
    the decimal portion of the Lat/Lon coordinates.
    To calculate the true lat/lon at any point, we add the offset below. 
    
   *Technically, the origin can be any point in earth we want to designate
    so, whatever it is, it will get added to the x,y thermal map coordinates.
'''
#the thermal matrix where the lift info will go
map_size = 10000 #covers a full degree, about 70nm
#initialize the map to zeros
thermal_map = {(0,0):0}



#origin points for the thermal map
lat_origin = -12.00
lon_origin = -76.00

''' The wind vector is used to calculate the thermal drift 
    and it is considered when reading thermal strength and
    locations for thermal graphics display
    * later may want to consider more wind layers
'''
wind_speed = 0  # m/s
wind_dir = 0    # radians
world_update = False # toggle on wind change


'''
   Thermal behaviour information
   There are many factors that afect thermal size and strenght as they move
   up from the ground to the higest point. 
   For now I will store those values here.. 

*http://www.skynomad.com/articles/height_bands.html
http://www.pilotoutlook.com/glider_flying/soaring_faster_and_farther
http://www.southerneaglessoaring.com/Storms/liftstrenghtgraph.htm
http://www.southerneaglessoaring.com/Storms/stormlift.htm
http://www.xcskies.com/map # may interact with this to get baseline data? 
'''
# list of thermal center at ground lat/lon coordinates. [lat,lon,thermal_size]
'''
    100,3890,7581) #Libmandi
     50,3994,7666) #SantaMaria
    150,3774,7815) #Intersection san bartolo
    300,3016,8448) #Interseccion senoritas
    350,4647,7516) #trebol de chilca
    500,7623,6061) #vor asia
'''
    #ask21 turn diameter at 60mph = 133m, 80mph = 420m



thermal_list  = [[-12.3890,-76.7581,100],[-12.3994,-76.7666,50],[-12.3774,-76.7815,150],[-12.3016,-76.8448,300],[-12.4647,-76.7516,350],[-12.7623,-76.6061,500]]

default_thermal_list  = [[-12.3890,-76.7581,100],[-12.3994,-76.7666,50],[-12.3774,-76.7815,150],[-12.3016,-76.8448,300],[-12.4647,-76.7516,350],[-12.7623,-76.6061,500]]


thermal_tops  = 1500 # maximum altitude for thermals in meters (may change based on temp/time of day/ etc. 
#thermal_height_band # size/strength of thermal depending on altitude
''' need to model size/strenght of thermal against:
        time of day    : average lift depends on sun angle over the earth. 
                         sunrise  - - | - - - - - -| - sunset
                                low        best         low 
                         
                         thermal tops depends on time of day
                         sunrise  - - | - - - - - -| - sunset
                                low        high       high

                                  
        temperature
        altitude band : average lift increases with altitude until 10% of thermal top where it starts decreasing
                        beggining of band is terrain altitude dependant... 
                        todo:adjust calcthermal to account for this..
                        
        raob ?
'''
#GUI state variables
thermals_visible = True

