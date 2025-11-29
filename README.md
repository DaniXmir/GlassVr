# GlassVr
glassvr is a way to use XR/AR glasses from xreal, viture etc, with 6dof in steamvr

the glasses are running like monitors, so you dont need the fancy ones with 6dof or even 3dof builtin, these features requires special software to be used that varies from manufacturer to manufacturer,
that also means that the screens are mirroring for both eye, not idle for vr but usable,

steamvr isn't designed for a "headset" like this but i found some workarounds

# Requirements
- glasses that can act like monitors, for you'r eyes ofcourse
- base stations and 1 vr controller(vive, index etc) or 1 vr tracker(vive, Tundra etc), to track you'r head

note: with something like the vive ultimate tracker you could skip needing base stations, but then you wont be able to track you'r controllers for you'r hands

# Optinal Hardware
- 2 additional controllers, one for each hand
- a way to attach you'r controller/tracker to you head, alignment isn't critical since you can adjust position and rotation offsets later
- steamvr watchman dongles, while not required, needed if you want to use your controllers wirelessly, one dongle per device

here is a cool video that explains what are dongles: https://www.youtube.com/watch?v=gmzmNvJFkSc

# Setup
1. download the .rar in the Releases tab and extract it, you will see 2 folders
2. put the "glassvedriver" folder in C:\Program Files (x86)\Steam\steamapps\common\SteamVR\drivers
3. make sure that you'r glasses are connected, set as the primary display and resolution is set to 1920x1080(even if you glasses support resolutions higher)
4. open steamvr
5. in "glassvrserver" folder, click on main.exe to launch the server

you should see a window called "Headset Window" and it should be copying one of you'r controller position and rotation

now you need to change some settings in the "settings.json"

	{
		#set to "controller" to track a controller, set to "tracker" to track a tracker
	    "controller/tracker": "controller",

		#which controller/tracker to track
	    "index": 1,

		#distance between eyes, increment/decrement until you'r contollers feel centered, set it to something like -0.2
	    "ipd": -0.2,

		#distance from the center of you'r tracker to you'r eyes, set it to something like -0.14
	    "head to eye dist": -0.14,

		#DO NOT USE "position x" and "position z", the rest are self explanatory
	    "offsets": {
	        "position x": 0,
	        "position y": 0.0,
	        "position z": 0.0,
	        "rotation yaw": -3.25,
	        "rotation pitch": 0.89,
	        "rotation roll": -2.0
	    }
	}
	
# Troubleshooting

C:\Program Files (x86)\Steam\config\steamvr.vrsettings

 "steamvr" : {
    "activateMultipleDrivers" : true
 }

credit
code used from https://github.com/r57zone/OpenVR-driver-for-DIY by r57zone
