# GlassVr
glassvr is an openvr driver that let you use XR/AR glasses with 6dof and even stereoscopic 3D in steamvr,
while steamvr isn't really designed for a "headset" like this, they work surprisingly well in it

showcase on youtube: https://www.youtube.com/watch?v=ySr_ktM-0Mo

join the discord! https://discord.gg/jyvWdKBpPj

# Installing
1. download the .rar in the Releases tab and extract it
2. run main.exe
3. in the Driver tab click "install"
now when you launch steamvr you should see a window called "Headset Window" and it should be copying one of you'r trackers position and rotation

to uninstall, simply click on "uninstall" in the Driver tab

note:
 - i only tested the driver on my vitrue pro xr but it should work no problem on other glasses like xreal etc
 - not every glasses out there support stereoscopic 3D(SBS), here is how to enable it on the viture pro xr
hold the button closest to the screen until the resolution change to 3840x1080@60, the problem is that its @60, 60hz in vr is not good so i dont recommend using it if you'r glasses cant at least do 90hz in that mode
<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_090401.jpg width="512">

there is a way to overclock the glasses to 3840x1080@90 but...
WARNING: this method will make you'r gpu driver unable to use 2D mode so do it at you'r own risk,
fix(if needed): uninstall you'r gpu driver in device manager
1) download cru https://customresolutionutility.net/ nvidia's or amd's custom resolution won't work here
2) add 3840x1080@90
3) click restart.exe

also try downgrading you'r firmware if you can, i found that older firmwares can be more stable
<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/hz2.png width="512">

# Requirements
- xr glasses or a monitors, for you'r eyes ofcourse
- vr controller or vr tracker, to track you'r head

base stations aren't required, they just the easiest to setup

# Optinal Hardware
- 2 additional controllers, one for each hand
- a way to attach you'r controller/tracker to you head, alignment isn't critical since you can adjust position and rotation offsets later
- steamvr watchman dongles(for vive, index etc controllres only), while not required, are needed if you want to use your controllers wirelessly, one dongle per device

here is a cool video that explains what are dongles: https://www.youtube.com/watch?v=gmzmNvJFkSc

the full setup should look something like this (glasses, 2 base stations, 3 controllers or 2 controllers and a tracker, 2 dongles, tracker mount)

<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_085109.jpg width="512">

# Mounting the controller/tracker
mount it as close to the center of you'r head as you can,
now as to how to mount it, that up to you, the most basic setup i could find is a hat and a shoe laces,
if you end up 3D printing something, please share it online so other could use it

<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_081836.jpg width="512">

here's my design: https://www.thingiverse.com/thing:7293001

<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20260211_174231.jpg width="512">

# Other features
tldr i was bored and added some cool features

 - controller emulation:

	emulate index controller with a tracker and a physical controller, supports xbox, joycons, ps4/5 etc
	
	demonstration: darth maul dual saber using only one controller:
	
	<a href="https://www.youtube.com/watch?v=AHyDTgIQ-1U">
	  <img src="https://img.youtube.com/vi/AHyDTgIQ-1U/maxresdefault.jpg" width="600" alt="Watch the video">
	</a>

 - hand tracking using a webcam(curl and splay only):

	use a webcam for hand tracking, tracker for 6dof and a physical controller for buttons, requires the OpenGloves driver
	
	1, download it from steam: https://store.steampowered.com/app/1574050/OpenGloves/

    2, and enable named pipe communication

	demonstration: webcam, joycon, vive wand

	<a href="https://www.youtube.com/watch?v=1IrDE8JJ0mk">
	  <img src="https://img.youtube.com/vi/1IrDE8JJ0mk/maxresdefault.jpg" width="600" alt="Watch the video">
	</a>

 - tracker emulation:

	convert old controllers to trackers

	demonstration(not video): using index controller to emulate a tracker

	<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/tracker%20emulation.png width="600">

# Troubleshooting
1. if you'r controllers not showing up, goto C:\Program Files (x86)\Steam\config\steamvr.vrsettings
and add "activateMultipleDrivers" : true

		 "steamvr" : {
			"activateMultipleDrivers" : true
		 }
3. weird flickering/objects not rendering in some games? specifically godot XR? set IPD to be greater than 0

# QNA
1. will this work with my (insert company name here aka, viture, xreal etc) glasses?
	
	yes, the driver doesn't care which glasses you have, literally any monitor will work

2. i don't have base station, but i do have quest controllers, can i use them?

   maybe, if you could find a way to use the controllers without the headset in steamvr
   
3. I only have 2 controllers...

   strap one to you'r head and the other to you'r hand, keep in mind that it will be visible, buttons will still work and rumble will be active

4. can i use the builtin 3DOF imu?

	no... check this project instead: https://docs.vertoxr.com/docs/features/steamvr/
   
5. linux?
	
	in the future, maybe

6. wireless?
	
	option 1. find a way to stream the "headset window" to your phone, maybe alvr or even Parsec?
	
	option 2. there are some "wireless hdmi 120hz" on amazon/aliexpress, but i dont know how good they actually are, especially for vr

7. any more quetions?
    
	ask them in the discord server: https://discord.gg/WbEqvHKs

