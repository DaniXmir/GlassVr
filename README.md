# GlassVr
glassvr is an openvr driver/server that let you use XR/AR glasses with 6dof and even stereoscopic 3D in steamvr,
while steamvr isn't really designed for a "headset" like this, they work surprisingly well in it

i only tested the driver on my vitrue pro xr but it should work no problem on other glasses like xreal etc

there are 4 different driver you can choose from,
<table border="1">
  <tr>
    <td>mono</td>
    <td>default</td>
  </tr>
  <tr>
    <td>mono</td>
    <td>wide</td>
  </tr>
  <tr>
    <td>stereo</td>
    <td>default</td>
  </tr>
  <tr>
    <td>stereo</td>
    <td>wide</td>
  </tr>
</table>

default/wide is the FOV,
 - default: is more 1:1 with reality but very narrow since the fov of the glasses is so small
 - wide: i recommend this one since you can see more

monoscopic/stereoscopic,
 - monoscopic: screen will mirror each other
 - stereoscopic: each screen renders its own image to give you the illusion of 3d

not every glasses out there support stereoscopic 3D, here is how to enable it on the viture pro xr
hold the button closest to the screen until the resolution change to 3840x1080@60, the problem is that its @60, 60hz in vr is not good so i dont recommend using it if you'r glasses cant at least do 90hz in that mode
<img src=https://github.com/DaniXmir/GlassVr/blob/master/media/20251130_090401.jpg width="512">

i recommend monoscopic wide if you'r glasses cant do more then 3840x1080@90+
and stereoscopic wide if they can,
the default fov is unusable

# Requirements
- glasses that can act like monitors, for you'r eyes ofcourse
- base stations and 1 vr controller(vive, index etc) or 1 vr tracker(vive, Tundra etc), to track you'r head

note: with something like the vive ultimate tracker you could skip needing base stations, but then you won't be able to track you'r controllers for you'r hands

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
1. download the .rar in the Releases tab and extract it, you will see 2 folders
2. in the "driver" folder, put you'r chosen driver "glassvedriver {mode} {resolutio} {fov}" folder in C:\Program Files (x86)\Steam\steamapps\common\SteamVR\drivers
3. make sure that you'r glasses are connected, set as the primary display and resolution is correct
4. connect you'r controllers and open steamvr
5. in "glassvrserver" folder, click on "main.exe" to launch the server

you should see a window called "Headset Window" and it should be copying one of you'r controller position and rotation

now you need to change some settings in the "settings.json"

	{
		#set to "controller" to track a controller, set to "tracker" to track a tracker
	    "controller/tracker": "controller",

		#which controller/tracker to track
	    "index": 1,

		#distance between eyes
	    "ipd": 0.0,

		#distance from the center of you'r head to you'r eyes
	    "head to eye dist": 0.0,

		#DO NOT USE "position x" and "position z"
	    "offsets": {
	        "position x": 0.0,
	        "position y": 0.0,
	        "position z": 0.0,
			
	        "rotation yaw": 0.0,
	        "rotation pitch": 0.0,
	        "rotation roll": 0.0
	    }
	}

# disabling the driver
delete or move "glassvedriver" from C:\Program Files (x86)\Steam\steamapps\common\SteamVR\drivers
(renaming won't work)

# Troubleshooting
1. if you controllers not showing up, goto C:\Program Files (x86)\Steam\config\steamvr.vrsettings
and add "activateMultipleDrivers" : true

		 "steamvr" : {
			"activateMultipleDrivers" : true
		 }
