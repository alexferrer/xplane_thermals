xplane_thermals
===============

Xplane plugin to generate more realistic thermals 

The current Xplane (Ver 10) thermal model is quite simplistic. This is an attempt to create a pluggin that simulates 
thermal of better quality

Basic concept:
Create a NxN matrix representing lat long and containing lift indexes for a given territory. 
While fliying, detect collision between the aircraft and the thermals, apply the lift to the aircraft.

Installation
This is a Python plugin, so the python interface is required. ( http://www.xpluginsdk.org/python_interface.htm )
As a helper, I am using Easy Dataref access class from Joan Perez i Cauhe, I am including the class on the sources


V 0.1 it works based on a 10x10 matrix that repeats itself. it works, but is just a sucky proof of concept.
