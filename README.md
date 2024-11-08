xplane_thermals - (Updated for Python 3)
===============

Author: Alex Ferrer
License: GPL 2014 / Updated Nov 2024


X-Plane plugin to generate more realistic thermals 

This updated plugin only works with the new Python3 plugin and XPlane 12 and above!

Basic concept:
Create a fixed or random list of thermals with lat,lon,thermal diameter, thermal strength.
While flying, detect collision between the aircraft and the thermals, apply the lift to the aircraft.


Advanced concepts already implemented:

- Regular Thermals (not dynamic lift) tend to have a strong core of lift followed by outward softer layers of lift.

- Thermals drift with the wind as they gain altitude. 

- Thermals rise till they reach cloudbase or the top of the lift. At this point they dwindle off. 

- When a wing of a plane hits a thermal and the other wing does not, the plane tends to roll against the lift.

- When the wing of the plane is on a roll, the thermal roll factor is reduced (less arm momentum) 

- Thermals gain and loose strength along with the height of the sun in the sky (accounting for seasons)


A random thermal generator menu allows the user to select quantity of thermals, size and strength. The thermal placement is random, but smart enough not to set thermals above water surfaces. 

A thermal visualization aid (shows markers where the thermals are) exists with an option to turn it on/off on the plugin menu.

UPDATE
-----
- Youtube videos showing the pluggin in action https://www.youtube.com/playlist?list=PLCOXBmOQk9UA55rzYTZvHnyQ_FopH_U9x
- Real clouds!!!
- Select thermal column visibility from generate thermal menu 
- Enable / Disable plugin for when you are not flying gliders
- Persistant menu preferences saved on exit or disable
- https://forums.x-plane.org/index.php?/forums/topic/225976-xppython3-v312-now-available/
- https://xppython3.readthedocs.io/en/stable/
- Load CSV hotspots from https://thermal.kk7.ch/ added. Download your fav. thermal hotspots and put it in your X-plane root directory. 



Enable/Disable Plugin Option

The Gliding Simulator plugin includes an Enable/Disable option in the menu. This feature allows you to activate the plugin when flying gliders to experience realistic thermal effects. When flying other types of aircraft, you can disable the plugin to prevent thermal effects from impacting your flight. This gives you flexibility to use the plugin only when it enhances your specific flight experience.

Persistent Configuration Options

The Gliding Simulator plugin offers Persistent Configuration Options, allowing you to save settings like Enable/Disable, Thermals On/Off, and various glider configuration options. These preferences are stored in an .ini file, so your settings are automatically loaded each time you start the plugin. This ensures a seamless experience without needing to reconfigure the plugin for each session.


Glider Config Menu Option

The Glider Config menu option lets you customize the forces applied to the glider during thermal encounters. You can adjust parameters like lift, thrust, and pitch in response to various thermal strengths, enabling a more realistic and tailored gliding experience. This fine-tuning helps simulate different thermal intensities and conditions for an immersive flight.

Load Thermals from CSV Files

The Load Thermals from CSV Files menu option enables you to import thermal hotspot data from CSV files, creating custom thermal environments in your simulator. You can download pre-made thermal hotspot files from sources like the thermal.kk7 website, or create your own CSV files with specific locations and conditions. This feature provides flexibility to tailor thermals to your flying area and preferences.

Thermal Rings On/Off Menu Option

The Thermal Rings On/Off menu option allows you to toggle the visibility of thermal column rings. These rings, which appear along the rising thermal, help beginner pilots locate and track thermals more easily. For a more realistic experience, you can turn off the thermal rings, providing a challenge for more experienced glider pilots.


TODOs
-----

- Thermals have cycles, begin, middle, end and they tend to keep a basic timming.

The idea is to simulate the begin, middle and end stages of a thermal that go on cycles throughout the day. 
Begin: after the sun heats the ground and a big parcel of humid air gets warm enough a giant "bubble" of hot air raises into the air (because hot air is lighter than the surrounding air) at this point the thermal is usually small in diameter and starts getting stronger. 

Middle: the "bubble" of hot air is already climbing, it gets wider and has the strongest lift

End: once the whole bubble has reached cloudbase, the air inside and outside the bubble are equal, so it stops moving up. but still has remaining lift until it eventually dies. 

The lengths of this cycles varies depending on temperature, humidity, altitude etc. Glider pilots learn to recognize this patterns and use them to know when to leave a thermal. 

- Thermal streets

Installation
------------

( https://xppython3.readthedocs.io/en/latest/index.html )
This is XPPython3 version 4 and includes both the X-Plane plugin as well as a private version of Python3. Unlike previous versions of XPPython3, you no longer need to install your own copy of Python.

For installation copy the XPLANE THERMALS Python files to the X-Plane Resources/plugins/PythonPlugins folder so that the Python plugin can find them.

Other than that, all is needed is PI_ThermalSim, thermal_model.py and world.py anything else is test stuff or helpers. 

V.04 Changes: 

Real clouds at cloudbase on top of thermals! (Thx to forums.x-plane.org @troopie for pointing me on the right direction!)

Menu options to :
Set the debug level 1 to 6 dumps info to XPPython3Log.txt (for devs & debug only) 
Configure the glider lift/roll/pitch response when on thermals and a 1 m/s calibrate mode for easier setup of your glider 



Older versions
--------------
V 0.3 has a nice menu to define thermal parameters, better thermal simulation, better performance and reduced memory space. 

All previous versions where Python 2.6 

V 0.2 (current) Is already quite usable. It has a matrix of 10000x10000 ~70nm^2 , implements all the concepts listed above. At this point there are several variables (wind, thermal tops, thermal generation) that are hardcoded and require changes of code if you wish to modify.

V 0.1 it works based on a 10x10 matrix that repeats itself. it works, but is just a sucky proof of concept.


About the author
----------------

I have about 25 years experience flying thermals on Gliders, Paragliders and Ultralight aircrafts. I've owned and flown (sp?) many diferent gliders from a very slow 1-26 to ASK-21.  I've flown extensively on the Texas plains and on the mountains of Peru, so I feel I've got a good idea of how a thermal should feel when you fly a glider on X-Plane. I hope that this plugin helps improve the glider flying experience on X-plane for all. 
