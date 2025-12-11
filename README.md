# GlassVr
glassvr is an openvr driver that let you use XR/AR glasses with 6dof and even stereoscopic 3D in steamvr,
while steamvr isn't really designed for a "headset" like this, they work surprisingly well in it

showcase on youtube: https://www.youtube.com/watch?v=ySr_ktM-0Mo

# Installing
1. download the .rar in the Releases tab and extract it
2. run main.exe
3. in the Driver tab click "install"
now when you launch steamvr you should see a window called "Headset Window" and it should be copying one of you'r trackers position and rotation

to uninstall, simply click on "uninstall" in the Driver tab

# note
 - i only tested the driver on my vitrue pro xr but it should work no problem on other glasses like xreal etc
 - not every glasses out there support stereoscopic 3D(SBS), here is how to enable it on the viture pro xr
hold the button closest to the screen until the resolution change to 3840x1080@60, the problem is that its @60, 60hz in vr is not good so i dont recommend using it if you'r glasses cant at least do 90hz in that mode
<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_090401.jpg width="512">

# Requirements
- xr glasses or a monitors, for you'r eyes ofcourse
- vr controller or vr tracker(base station aren't needed), to track you'r head

for now the only supported method of tracking is by copying a trackers/controller positon and rotation from steamvr to the headset
this means you can use anything that steamvr can see, as long as you can disable you'r actual headset,
i am experimenting with other tracking methods like SlimeVR, cameras, lights, magnets and more

# Optinal Hardware
- 2 additional controllers, one for each hand
- a way to attach you'r controller/tracker to you head, alignment isn't critical since you can adjust position and rotation offsets later
- steamvr watchman dongles(for vive, index etc controllres only), while not required, needed if you want to use your controllers wirelessly, one dongle per device

here is a cool video that explains what are dongles: https://www.youtube.com/watch?v=gmzmNvJFkSc

the full setup should look something like this (glasses, 2 base stations, 3 controllers or 2 controllers and a tracker, 2 dongles, tracker mount)

<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_085109.jpg width="512">

# Mounting the controller/tracker
mount it as close to the center of you'r head as you can,
now as to how to mount it, that up to you, the most basic setup i could find is a hat and a shoe laces,
if you end up 3D printing something, please share it online so other could use it

<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_081836.jpg width="512">

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
   
4. I only have 2 controllers

   strap one to you'r head and the other to you'r hand, keep in mind that it will be visible, buttons will still work and rumble will be active

5. can i use the built in 3DOF, dont they already support that?

	check this project: https://docs.vertoxr.com/docs/features/steamvr/

   	that project allows access to the imu and has some steamvr support, maybe in the future ill add 3DOF support,
	i had another idea of forwarding imu data to slimeVR and letting it calculate a 6DOF position
   
7. linux?
	
	in the furure, maybe

8. wireless?
	
	option 1. find a way to stream the "headset window" to your phone, Parsec could work, or alvr maybe?
	
	option 2. there are some "wireless hdmi 120hz" on amazon/aliexpress, but i dont know how good they actually are, especially for vr
