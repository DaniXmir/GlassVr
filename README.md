# GlassVr
glassvr is an openvr driver that let you use XR/AR glasses with 6dof and even stereoscopic 3D in steamvr,
while steamvr isn't really designed for a "headset" like this, they work surprisingly well in it

showcase on youtube: https://www.youtube.com/watch?v=ySr_ktM-0Mo

i only tested the driver on my vitrue pro xr but it should work no problem on other glasses like xreal etc

there are 2 thing you will need to download, 
1. server: copies one of you'r controller/tracker position and rotation and applies it to the glasses
2. driver: tells steamvr what to display in you'r glasses

note: not every glasses out there support stereoscopic 3D(SBS), here is how to enable it on the viture pro xr
hold the button closest to the screen until the resolution change to 3840x1080@60, the problem is that its @60, 60hz in vr is not good so i dont recommend using it if you'r glasses cant at least do 90hz in that mode
<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_090401.jpg width="512">

# Requirements
- glasses that can act like monitors, for you'r eyes ofcourse
- base stations and 1 vr controller(vive, index etc) or 1 vr tracker(vive, Tundra etc), to track you'r head

note: you dont need base stations, they are just easy to set up, maybe a full set of slimevr trackers could work...

# Optinal Hardware
- 2 additional controllers, one for each hand
- a way to attach you'r controller/tracker to you head, alignment isn't critical since you can adjust position and rotation offsets later
- steamvr watchman dongles, while not required, needed if you want to use your controllers wirelessly, one dongle per device

here is a cool video that explains what are dongles: https://www.youtube.com/watch?v=gmzmNvJFkSc

the full setup should look something like this (glasses, 2 base stations, 3 controllers or 2 controllers and a tracker, 2 dongles, tracker mount)

<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_085109.jpg width="512">

# Mounting the controller/tracker
mount it as close to the center of you'r head as you can,
now as to how to mount it, that up to you, the most basic setup i could find is a hat and a shoe laces,
if you end up 3D printing something, please share it online so other could use it

<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_081836.jpg width="512">

# PC Setup
1. download the .rar in the Releases tab and extract it
2. run main.exe
3. in the Driver tab click install

now when you launch steamvr you should see a window called "Headset Window" and it should be copying one of you'r trackers position and rotation

# uninstall the driver
in the Driver tab click uninstall

# Troubleshooting
1. if you'r controllers not showing up, goto C:\Program Files (x86)\Steam\config\steamvr.vrsettings
and add "activateMultipleDrivers" : true

		 "steamvr" : {
			"activateMultipleDrivers" : true
		 }

# QNA
1. will this work with my (insert company name here aka, viture, xreal etc) glasses?
	
	yes, the driver doesn't care which glasses you have, literally any monitor will work

2. i don't have base station, but i do have a quest headset

   maybe, if you could find a way to use the controllers without the headset

4. linux?
	
	in the furure, maybe

5. wireless?
	
	option 1. find a way to stream the "headset window" to your phone, Parsec could work
	
	option 2. search "wireless hdmi 120hz" on amazon/aliexpress

6. I only have 2 controllers

   strap one to you'r head and the other to you'r hand, keep in mind that it will be visible, buttons will still work and rumble will be active
