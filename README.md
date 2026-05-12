# GlassVr(name work in progress)
is a super modular openvr driver that let you emulate vr devices like a headset, controllers and trackers with hardware that you already own! 
i originally made this driver to create a super light headset using my XR glasses and a base station tracker but since i added a lot more features!

showcase on youtube: https://www.youtube.com/watch?v=LaRQ5dUw4bU

also join the discord! https://discord.gg/jyvWdKBpPj

# Installing
1. download the .rar in the Releases tab and extract it
2. run main.exe
3. in the Driver tab click "install"

to uninstall, simply click on "uninstall" in the Driver tab
youll also need to do lots of configuring because of the modular approach of the project

# Some Features:
emulating an headset with xr glasses imu(only viture glasses are supported for now) or a controller gyro like strapping a joycon to a hat for 3dof with static offsets for position
		
<a href="https://www.youtube.com/watch?v=K8fJ-rsfZ1U">
  <img src="https://img.youtube.com/vi/K8fJ-rsfZ1U/maxresdefault.jpg" width="600" alt="Watch the video">
</a>

pcvr hand tracking with just a normal camera! you can also emulate input with keyboard and mouse or physical controllers that compatible with SDL3(basically everything)
lots of people suggested using 2 computer mice for each hand.
	
<a href="https://www.youtube.com/watch?v=mYdC2gVEi6Y">
  <img src="https://img.youtube.com/vi/mYdC2gVEi6Y/maxresdefault.jpg" width="600" alt="Watch the video">
</a>

using old controllers as trackers by copying their position and rotation! this method does not require reprogramming the controller, useful if your old controller have a dead usb port like my index one

<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/tracker%20emulation.png width="600">

and many more!
also position and rotation can be emulated independently for each device allowing for lots of combinations!

# Custom Hardware:
and if thats not enough for you, you can also send data yourself with UDP or named pipes, 
with more communication protocols coming soon like bluetooth and serial

a common use case for this would be to build a custom controller with an arduino or esp32, lets say you only want to wire flex sensors and a gyro, you can use only the position part of the hand tracking or use a base station tracker and a joycon for the other inputs, or you wired everything and run out gpio ports? you could use 2 or more boards! like one for input and the other for skeletal, 
index controller capacitive buttons are also supported so for full emulation youll need at least 9 digital and 9 analog ports, add 5 more analog for splay

python examples for UDP and nammed pipes are available: https://github.com/DaniXmir/GlassVr/tree/master/examples/python
with arduino coming later

ideally you would want to build your own driver but i can see some use cases that it would be kinda overkill, 
like prototyping or a fun weekend project, or you just scared of c++ lol

# The Boring Technical Staff...
the driver is composed of 2 parts, the python "server"/ui side and the C++ driver side, 
the python side isnt just a frontend, its used in some modes like hand tracking or controller input emulation with SDL3, 
its sends its data via named pipes, these pipes can also be hijacked if you want to send custom data see examples: https://github.com/DaniXmir/GlassVr/tree/master/examples/python

# Building:
you can figure this out i believe in you ;P 
just keep in mind that i used viture sdk so youll need to get the .h files from their site, if you dont care about that feature just press ctrl+f and delete everything with "//viture-"

# Contributing:
idk

# Roadmap:
 - option to emulate htc vive and oculus touch controllers (with maybe also steam frame controllers?)
 - bluetooth and serial communication
 - playspace offsets for emulated devices
 - android app with ARcore

# Troubleshooting
1. if you'r controllers not showing up, goto C:\Program Files (x86)\Steam\config\steamvr.vrsettings
and add "activateMultipleDrivers" : true

		 "steamvr" : {
			"activateMultipleDrivers" : true
		 }
3. weird flickering/objects not rendering in some games? specifically godot XR? set IPD to be greater than 0

# QnA
1. linux?

	in the future... maybe.. (properly)
