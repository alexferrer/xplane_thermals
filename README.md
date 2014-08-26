xplane_thermals
===============
Author: Alex Ferrer
License: GPL 2014


Xplane plugin to generate more realistic thermals 

The current Xplane (Ver 10.30+) thermal model is quite simplistic. This is an attempt to create a pluggin that simulates thermal of better realism

Basic concept:
Create a fixed or random list of thermals with lat,lon,thermal diameter, thermal strength
While fliying, detect collision between the aircraft and the thermals, apply the lift to the aircraft.


Advanced concepts already implemented:
Regular Thermals (not dynamic lift) tend to have a strong core of lift followed by outward softer layers of lift. Thermals drift with the wind as they gain altitude. 
Thermals rise till they reach cloudbase or the top of the lift. At this point they dwindle off. 
When a wing of a plane hits a thermal and the other wing does not, the plane tends to roll against the lift.
When the wing of the plane is on a roll, the thermal roll factor is reduced (less arm momentum) 
Thermals gain and loose strength along with the height of the sun in the sky

A random thermal generator menu allows the user to select quantity of thermals, size and strength. The thermal placement is random, but smart enough not to set thermals above water surfaces. 

A thermal visualization aid (shows markers where the thermals are) exists with an option to turn it on/off on the plugin menu

Todo:
Thermals have cycles, begin, middle, end and they tend to keep a basic timming.

Installation
This is a Python plugin, so the python interface is required. ( http://www.xpluginsdk.org/python_interface.htm )
As a helper, I am using Easy Dataref access class from Joan Perez i Cauhe, and I am including the class on the sources. 
Other than that, all is needed is PI_ThermalSym, thermal_model.py and world.py anything else is test stuff or helpers. 

V 0.3 has a nice menu to define thermal parameters, better thermal simulation, better performance and reduced memory space. 

V 0.2 (current) Is already quite usable. It has a matrix of 10000x10000 ~70nm^2 , implements all the concepts listed above. At this point there are several variables (wind, thermal tops, thermal generation) that are hardcoded and require changes of code if you wish to modify.

V 0.1 it works based on a 10x10 matrix that repeats itself. it works, but is just a sucky proof of concept.


About the author: 
I have about 20 years experience flying thermals on Gliders, Paragliders and Ultralight aircrafts. I've owned and flown (sp?) many diferent gliders from a very slow 1-26 to ASK-21.  I've flown extensively on the Texas plains and on the mountains of Peru, so I feel I've got a good idea of how a thermal should feel when you fly a glider on Xplane. I hope that this plugin helps improve the glider flying experience on Xplane for all. 


