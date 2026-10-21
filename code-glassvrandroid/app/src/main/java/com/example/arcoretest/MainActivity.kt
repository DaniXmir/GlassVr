//TODO: add an option for holding the phone inverted(camera facing user) tracking seems to be ok this way too, its easier to press the vol buttons this way
//TODO: add offsets in ui and add other offsets like yaw and roll in both orientations
//TODO: add 3dof only (low priority)
//TODO: make browser layout remember if it was selected last and open on bootup
package com.example.GlassVR

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.os.Bundle
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.ui.input.pointer.pointerInput

import com.google.ar.core.Config
import com.google.ar.core.Frame
import com.google.ar.core.Session
import com.google.ar.core.TrackingState
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.nio.ByteOrder
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10
import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.sin

import kotlin.math.roundToInt
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.IntOffset

import coil.compose.AsyncImage
import coil.request.ImageRequest
import coil.decode.GifDecoder

import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import android.view.KeyEvent

import android.widget.Toast
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable

import android.app.AlertDialog
import android.view.ContextThemeWrapper

import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType

import androidx.compose.material3.Text
import androidx.compose.ui.draw.alpha

import android.graphics.BitmapFactory
import com.google.ar.core.AugmentedImage
import com.google.ar.core.AugmentedImageDatabase
import android.util.Log

class MainActivity : ComponentActivity() {
    @Volatile var useQr = false
    @Volatile var qrSizeMeters = 0.15
    @Volatile var waitingForQrReset = false
    var InEdit by mutableStateOf(false)
    var layoutRefreshTrigger by mutableStateOf(0)

    val arSessionState = mutableStateOf<Session?>(null)
    lateinit var glSurfaceView: GLSurfaceView
    var renderer: ArRenderer? = null

    @Volatile var isVertical = false
    @Volatile var sendResetPacket = false
    @Volatile var resetFramesRemaining = 0
    @Volatile var originAnchor: com.google.ar.core.Anchor? = null

    @Volatile var latestTx = 0.0
    @Volatile var latestTy = 0.0
    @Volatile var latestTz = 0.0
    @Volatile var latestQw = 1.0
    @Volatile var latestQx = 0.0
    @Volatile var latestQy = 0.0
    @Volatile var latestQz = 0.0
    @Volatile var poseReady = false

    @Volatile var PitchOffset = -90.0

    // which controller the driver is emulating ("index", "touch", "vive", "frame"), needs to match "con type" on the pc, else will act weird
    // it decides which input packet gets sent (idx / itc / ive / ifm)
    @Volatile var conType = "touch"

    @Volatile var a = false
    @Volatile var b = false
    @Volatile var system = false
    @Volatile var select = false
    @Volatile var bumper = false
    @Volatile var yUp = false
    @Volatile var aDown = false
    @Volatile var xLeft = false
    @Volatile var bRight = false
    @Volatile var joy_x = 0.0
    @Volatile var joy_y = 0.0
    @Volatile var joy_btn = false
    @Volatile var touch_x = 0.0
    @Volatile var touch_y = 0.0
    @Volatile var touch_force = 0.0
    @Volatile var trigger = 0.0

    @Volatile var flexions = DoubleArray(20) { 0.0 }
    @Volatile var splays = DoubleArray(5) { 0.0 }
    @Volatile var pinky = 0.0
    @Volatile var middle = 0.0
    @Volatile var ring = 0.0
    @Volatile var grip = false

    @Volatile var volUpAction = HardwareAction.NONE
    @Volatile var volDownAction = HardwareAction.NONE
    lateinit var sharedPrefs: android.content.SharedPreferences

    @Volatile var ShowNav = "both"
    @Volatile var showNavHiddenToast = true

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        val action = when (keyCode) {
            KeyEvent.KEYCODE_VOLUME_UP -> volUpAction
            KeyEvent.KEYCODE_VOLUME_DOWN -> volDownAction
            else -> return super.onKeyDown(keyCode, event)
        }
        when (action) {
            HardwareAction.TRIGGER -> { trigger = 1.0 }
            HardwareAction.GRIP_HOLD -> { grip = true }
            HardwareAction.GRIP_TOGGLE -> { if (event?.repeatCount == 0) grip = !grip }
            HardwareAction.RESET -> { if (event?.repeatCount == 0) resetSession() }
            HardwareAction.NONE -> return super.onKeyDown(keyCode, event)
        }
        return true
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
        val action = when (keyCode) {
            KeyEvent.KEYCODE_VOLUME_UP -> volUpAction
            KeyEvent.KEYCODE_VOLUME_DOWN -> volDownAction
            else -> return super.onKeyUp(keyCode, event)
        }
        when (action) {
            HardwareAction.TRIGGER -> { trigger = 0.0 }
            HardwareAction.GRIP_HOLD -> { grip = false }
            HardwareAction.GRIP_TOGGLE -> {}
            HardwareAction.RESET -> {}
            HardwareAction.NONE -> return super.onKeyUp(keyCode, event)
        }
        return true
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge(navigationBarStyle = SystemBarStyle.dark(scrim = Color.Black.toArgb()))
        super.onCreate(savedInstanceState)
        setContent {
            val context = LocalContext.current
            var hasPermission by remember {
                mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED)
            }
            val view = LocalView.current
            SideEffect {
                val window = (view.context as? ComponentActivity)?.window ?: return@SideEffect
                val controller = WindowCompat.getInsetsController(window, view)
                controller.hide(WindowInsetsCompat.Type.systemBars())
                controller.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            }
            val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted -> hasPermission = granted }
            LaunchedEffect(Unit) { if (!hasPermission) launcher.launch(Manifest.permission.CAMERA) }

            if (hasPermission) {
                Box(modifier = Modifier.fillMaxSize()) {
                    AndroidView(
                        modifier = Modifier.fillMaxSize(),
                        factory = { ctx ->
                            GLSurfaceView(ctx).also { view ->
                                glSurfaceView = view
                                view.preserveEGLContextOnPause = true
                                view.setEGLContextClientVersion(2)
                                val r = ArRenderer(this@MainActivity)
                                renderer = r
                                view.setRenderer(r)
                                view.renderMode = GLSurfaceView.RENDERMODE_CONTINUOUSLY
                            }
                        }
                    )
                    AROverlayUI(activity = this@MainActivity)
                }
            } else {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Camera permission required", color = Color.White)
                }
            }

            sharedPrefs = getSharedPreferences("GlassVrSettings", MODE_PRIVATE)
            volUpAction = HardwareAction.valueOf(sharedPrefs.getString("volUp", HardwareAction.NONE.name)!!)
            volDownAction = HardwareAction.valueOf(sharedPrefs.getString("volDown", HardwareAction.NONE.name)!!)
        }
    }

    fun resetSession() {
        glSurfaceView.queueEvent {
            try {
                originAnchor?.detach()
                originAnchor = null
                poseReady = false
                if (useQr) waitingForQrReset = true else resetFramesRemaining = 10
            } catch (e: Exception) { e.printStackTrace() }
        }
    }

    override fun onResume() {
        super.onResume()
        if (::glSurfaceView.isInitialized) glSurfaceView.onResume()
    }
    override fun onPause() {
        super.onPause()
        if (::glSurfaceView.isInitialized) glSurfaceView.onPause()
        arSessionState.value?.pause()
    }
    override fun onDestroy() {
        super.onDestroy()
        arSessionState.value?.close()
        arSessionState.value = null
    }
}

class ArRenderer(private val activity: MainActivity) : GLSurfaceView.Renderer {
    val cameraTextureId = IntArray(1)
    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        GLES20.glGenTextures(1, cameraTextureId, 0)
        GLES20.glBindTexture(0x8D65, cameraTextureId[0])
        GLES20.glTexParameteri(0x8D65, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glTexParameteri(0x8D65, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glTexParameteri(0x8D65, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_NEAREST)
        GLES20.glTexParameteri(0x8D65, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_NEAREST)
    }
    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
        GLES20.glViewport(0, 0, width, height)
        activity.arSessionState.value?.setDisplayGeometry(0, width, height)
    }
    override fun onDrawFrame(gl: GL10?) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        val session = activity.arSessionState.value ?: return
        try {
            val frame: Frame = session.update()
            val camera = frame.camera
            if (camera.trackingState == TrackingState.TRACKING) {
                if (activity.useQr) {
                    if (activity.waitingForQrReset) {
                        val images = session.getAllTrackables(AugmentedImage::class.java)
                        for (image in images) {
                            Log.d("GlassVR-QR", "image=${image.name} state=${image.trackingState} method=${image.trackingMethod}")
                            if (image.trackingState == TrackingState.TRACKING &&
                                image.trackingMethod == AugmentedImage.TrackingMethod.FULL_TRACKING) {
                                activity.originAnchor = image.createAnchor(image.centerPose)
                                activity.waitingForQrReset = false
                                Log.d("GlassVR-QR", "anchor set from QR")
                                break
                            }
                        }
                        if (images.isEmpty()) Log.d("GlassVR-QR", "no augmented images in database/session")
                    }
                } else if (activity.originAnchor == null) {
                    val cp = camera.pose
                    val anchorPose = if (activity.isVertical) {
                        val qw = cp.qw(); val qx = cp.qx(); val qy = cp.qy(); val qz = cp.qz()
                        val pw = 0.7071067811865476f; val pz = 0.7071067811865476f
                        com.google.ar.core.Pose(
                            floatArrayOf(cp.tx(), cp.ty(), cp.tz()),
                            floatArrayOf(qx*pw+qy*pz, qy*pw-qx*pz, qz*pw+qw*pz, qw*pw-qz*pz)
                        )
                    } else { cp }
                    activity.originAnchor = session.createAnchor(anchorPose)
                }
                val anchor = activity.originAnchor ?: return
                val relativePose = anchor.pose.inverse().compose(camera.pose)
                activity.latestTx = relativePose.tx().toDouble()
                activity.latestTy = relativePose.ty().toDouble()
                activity.latestTz = relativePose.tz().toDouble()
                activity.latestQw = relativePose.qw().toDouble()
                activity.latestQx = relativePose.qx().toDouble()
                activity.latestQy = relativePose.qy().toDouble()
                activity.latestQz = relativePose.qz().toDouble()
                activity.poseReady = true
            }
        } catch (e: Exception) { e.printStackTrace() }
    }
}

fun quatMul(qw: Double, qx: Double, qy: Double, qz: Double, pw: Double, px: Double, py: Double, pz: Double): DoubleArray = doubleArrayOf(
    qw*pw-qx*px-qy*py-qz*pz, qw*px+qx*pw+qy*pz-qz*py, qw*py-qx*pz+qy*pw+qz*px, qw*pz+qx*py-qy*px+qz*pw
)

const val CLICK_AT = 0.95
const val CAP_AT = 0.05

private fun ByteBuffer.putTag(tag: String): ByteBuffer = put(tag.toByteArray(Charsets.US_ASCII))
private fun ByteBuffer.putBools(vararg values: Boolean): ByteBuffer {
    for (v in values) put(if (v) 1.toByte() else 0.toByte())
    return this
}
private fun ByteBuffer.putDoubles(vararg values: Double): ByteBuffer {
    for (v in values) putDouble(v)
    return this
}

fun buildQrDatabase(session: Session, activity: MainActivity): AugmentedImageDatabase {
    val db = AugmentedImageDatabase(session)
    try {
        activity.assets.open("qr_origin.png").use { stream ->
            val bitmap = BitmapFactory.decodeStream(stream)
            if (bitmap == null) {
                Log.e("GlassVR-QR", "decodeStream returned null for qr_origin.png")
            } else {
                val idx = db.addImage("origin_qr", bitmap, activity.qrSizeMeters.toFloat())
                Log.d("GlassVR-QR", "added origin_qr at index $idx, size ${bitmap.width}x${bitmap.height}")
            }
        }
    } catch (e: Exception) {
        Log.e("GlassVR-QR", "failed to load qr_origin.png from assets", e)
    }
    return db
}

enum class HardwareAction(val label: String) {
    NONE("none"), TRIGGER("trigger"), GRIP_HOLD("grip(hold)"), GRIP_TOGGLE("grip(toggle)"), RESET("reset")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AROverlayUI(activity: MainActivity) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("ar_settings", Context.MODE_PRIVATE) }
    val configuration = LocalConfiguration.current
    val isLandscape = configuration.screenWidthDp > configuration.screenHeightDp

    var pitchOffset by remember { mutableStateOf(prefs.getFloat("PitchOffset", -90.0f).toDouble()) }
    LaunchedEffect(pitchOffset) { activity.PitchOffset = pitchOffset; prefs.edit().putFloat("PitchOffset", pitchOffset.toFloat()).apply() }

    var showNavState by remember { mutableStateOf(prefs.getString("show_nav", "both") ?: "both") }
    LaunchedEffect(showNavState) { activity.ShowNav = showNavState; prefs.edit().putString("show_nav", showNavState).apply() }

    var showNavHiddenToast by remember { mutableStateOf(prefs.getBoolean("show_nav_hidden_toast", true)) }
    LaunchedEffect(showNavHiddenToast) { prefs.edit().putBoolean("show_nav_hidden_toast", showNavHiddenToast).apply() }
    LaunchedEffect(isLandscape) {
        val navIsHidden = when (showNavState) { "horizontal" -> !isLandscape; "vertical" -> isLandscape; else -> false }
        if (navIsHidden && showNavHiddenToast)
            Toast.makeText(context, "Navbar is hidden, rotate your phone! (Toast can be disable in settings)", Toast.LENGTH_LONG).show()
    }

    var volUpState by remember { mutableStateOf(HardwareAction.valueOf(prefs.getString("volUp", HardwareAction.NONE.name) ?: HardwareAction.NONE.name)) }
    var volDownState by remember { mutableStateOf(HardwareAction.valueOf(prefs.getString("volDown", HardwareAction.NONE.name) ?: HardwareAction.NONE.name)) }
    var volUpDropdownExpanded by remember { mutableStateOf(false) }
    var volDownDropdownExpanded by remember { mutableStateOf(false) }
    LaunchedEffect(volUpState) { prefs.edit().putString("volUp", volUpState.name).apply(); activity.volUpAction = volUpState }
    LaunchedEffect(volDownState) { prefs.edit().putString("volDown", volDownState.name).apply(); activity.volDownAction = volDownState }

    var ipAddress by remember { mutableStateOf(prefs.getString("ip", null) ?: "255.255.255.255") }
    LaunchedEffect(ipAddress) { prefs.edit().putString("ip", ipAddress).apply() }

    var port by remember { mutableStateOf(prefs.getString("port", null) ?: "9001") }
    LaunchedEffect(port) { prefs.edit().putString("port", port).apply() }

    var conTypeState by remember { mutableStateOf(prefs.getString("con_type", "touch") ?: "touch") }
    LaunchedEffect(conTypeState) { activity.conType = conTypeState; prefs.edit().putString("con_type", conTypeState).apply() }

    var isVertical by remember { mutableStateOf(prefs.getBoolean("vertical", false)) }
    LaunchedEffect(isVertical) { activity.isVertical = isVertical; prefs.edit().putBoolean("vertical", isVertical).apply() }

    var isStreaming by remember { mutableStateOf(prefs.getBoolean("streaming", false)) }
    LaunchedEffect(isStreaming) { prefs.edit().putBoolean("streaming", isStreaming).apply() }

    var showBrowser by remember { mutableStateOf(false) }
    var showHeadset by remember { mutableStateOf(false) }

    var browserUrl by remember { mutableStateOf(prefs.getString("browser_url", null) ?: "192.168.50.83:9999") }
    LaunchedEffect(browserUrl) { prefs.edit().putString("browser_url", browserUrl).apply() }

    var videoPort by remember { mutableStateOf(prefs.getString("video_port", "9990") ?: "9990") }
    LaunchedEffect(videoPort) { prefs.edit().putString("video_port", videoPort).apply() }

    var useQrState by remember { mutableStateOf(prefs.getBoolean("use_qr", false)) }
    LaunchedEffect(useQrState) { activity.useQr = useQrState; prefs.edit().putBoolean("use_qr", useQrState).apply() }

    var qrSizeStr by remember { mutableStateOf(prefs.getFloat("qr_size", 0.15f).toString()) }
    LaunchedEffect(qrSizeStr) { activity.qrSizeMeters = qrSizeStr.toDoubleOrNull() ?: activity.qrSizeMeters; prefs.edit().putFloat("qr_size", activity.qrSizeMeters.toFloat()).apply() }

    var settingsExpanded by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        if (!prefs.getBoolean("did_first_setup", false)) {
            val editor = prefs.edit()
            allButtonIds.forEach { id -> editor.putBoolean("${id}_isDisabled", true) }
            editor.putBoolean("did_first_setup", true)
            editor.apply()
            activity.layoutRefreshTrigger++
        }
        if (!prefs.getBoolean("did_setup_controller_types", false)) {
            val editor = prefs.edit()
            newButtonIds.forEach { id -> if (!prefs.contains("${id}_isDisabled")) editor.putBoolean("${id}_isDisabled", true) }
            editor.putBoolean("did_setup_controller_types", true)
            editor.apply()
            activity.layoutRefreshTrigger++
        }
    }

    LaunchedEffect(port) {
        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            var listenSocket: DatagramSocket? = null
            try {
                val portInt = port.toIntOrNull() ?: 9002
                listenSocket = DatagramSocket(portInt).apply { broadcast = true }
                val buffer = ByteArray(256)
                val packet = DatagramPacket(buffer, buffer.size)
                while (true) {
                    listenSocket.receive(packet)
                    val msg = String(packet.data, 0, packet.length, Charsets.UTF_8).trim()
                    if (msg == "RESET") activity.resetSession()
                }
            } catch (e: Exception) { e.printStackTrace() } finally { listenSocket?.close() }
        }
    }

    LaunchedEffect(isStreaming) {
        if (isStreaming) {
            activity.glSurfaceView.queueEvent {
                try {
                    if (activity.arSessionState.value == null) {
                        val textureId = activity.renderer?.cameraTextureId?.get(0) ?: 0
                        val session = Session(activity).apply {
                            val config = Config(this)
                            config.updateMode = Config.UpdateMode.LATEST_CAMERA_IMAGE
                            if (activity.useQr) {
                                config.focusMode = Config.FocusMode.AUTO
                                config.augmentedImageDatabase = buildQrDatabase(this, activity)
                            }
                            configure(config)
                            setCameraTextureName(textureId)
                            resume()
                        }
                        activity.arSessionState.value = session
                    } else { activity.arSessionState.value?.resume() }
                } catch (e: Exception) { e.printStackTrace() }
            }
        } else {
            activity.glSurfaceView.queueEvent {
                try {
                    activity.arSessionState.value?.pause()
                    activity.arSessionState.value?.close()
                    activity.arSessionState.value = null
                    activity.poseReady = false
                } catch (e: Exception) { e.printStackTrace() }
            }
        }
    }

    LaunchedEffect(isStreaming) {
        if (!isStreaming) return@LaunchedEffect
        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            val socket = DatagramSocket()
            val address = InetAddress.getByName(ipAddress)
            val portInt = port.toIntOrNull() ?: 9001
            val posBuffer = ByteBuffer.allocate(3 + 24).order(ByteOrder.LITTLE_ENDIAN)
            val rotBuffer = ByteBuffer.allocate(3 + 32).order(ByteOrder.LITTLE_ENDIAN)
            val extraBuffer = ByteBuffer.allocate(3 + 1).order(ByteOrder.LITTLE_ENDIAN)
            val s = sin(Math.PI / 4); val c = cos(Math.PI / 4)
            val indexBuffer = ByteBuffer.allocate(3 + 12 + 8 * 8).order(ByteOrder.LITTLE_ENDIAN)   // idx
            val touchBuffer = ByteBuffer.allocate(3 + 8 + 4 * 8).order(ByteOrder.LITTLE_ENDIAN)    // itc
            val viveBuffer = ByteBuffer.allocate(3 + 6 + 3 * 8).order(ByteOrder.LITTLE_ENDIAN)     // ive
            val frameBuffer = ByteBuffer.allocate(3 + 20 + 4 * 8).order(ByteOrder.LITTLE_ENDIAN)   // ifm
            val skeletalBuffer = ByteBuffer.allocate(3 + 25 * 8).order(ByteOrder.LITTLE_ENDIAN)

            while (isStreaming) {
                val tx = activity.latestTx; val ty = activity.latestTy; val tz = activity.latestTz
                var qw = activity.latestQw; var qx = activity.latestQx; var qy = activity.latestQy; var qz = activity.latestQz

                if (activity.isVertical) {
                    val r = quatMul(qw, qx, qy, qz, c, 0.0, 0.0, -s)
                    val pOff = Math.toRadians(pitchOffset); val rOff = Math.toRadians(180.0)
                    val cp = cos(pOff * 0.5); val sp = sin(pOff * 0.5)
                    val cr = cos(rOff * 0.5); val sr = sin(rOff * 0.5)
                    val finalR = quatMul(r[0], r[1], r[2], r[3], cp*cr, sp*cr, -sp*sr, cp*sr)
                    qw = finalR[0]; qx = finalR[1]; qy = finalR[2]; qz = finalR[3]
                }

                extraBuffer.clear(); extraBuffer.putTag("ext")
                val isResetting = activity.resetFramesRemaining > 0
                extraBuffer.putBools(isResetting)
                socket.send(DatagramPacket(extraBuffer.array(), extraBuffer.position(), address, portInt))
                if (activity.resetFramesRemaining > 0) activity.resetFramesRemaining--

                posBuffer.clear(); posBuffer.putTag("pos")
                posBuffer.putDoubles(tx, ty, tz)
                socket.send(DatagramPacket(posBuffer.array(), posBuffer.position(), address, portInt))

                rotBuffer.clear(); rotBuffer.putTag("rot")
                rotBuffer.putDoubles(qw, qx, qy, qz)
                socket.send(DatagramPacket(rotBuffer.array(), rotBuffer.position(), address, portInt))

                val trig = activity.trigger
                val trigBtn = trig >= CLICK_AT
                val trigCap = trigBtn || trig > CAP_AT
                val isAnyFingerActive = activity.middle > 0.0 || activity.ring > 0.0 || activity.pinky > 0.0
                val gripOn = activity.grip || isAnyFingerActive
                val gripVal = if (gripOn) 1.0 else 0.0
                val joyX = activity.joy_x; val joyY = activity.joy_y
                val joyBtn = activity.joy_btn
                val joyCap = joyBtn || abs(joyX) > 0.1 || abs(joyY) > 0.1
                val a = activity.a; val b = activity.b; val system = activity.system
                val select = activity.select

                when (activity.conType) {
                    "touch" -> {
                        // touch: a_x/b_y are A/B on the right hand and X/Y on the left, no touchpad
                        touchBuffer.clear(); touchBuffer.putTag("itc")
                        touchBuffer.putBools(system, a, a, b, b, trigCap, joyBtn, joyCap)
                        touchBuffer.putDoubles(trig, gripVal, joyX, joyY)
                        socket.send(DatagramPacket(touchBuffer.array(), touchBuffer.position(), address, portInt))
                    }
                    "vive" -> {
                        // vive: the trackpad is the joystick (touchpad is used if the joystick is idle), grip is click only
                        val joyActive = joyX != 0.0 || joyY != 0.0
                        val padX = if (joyActive) joyX else activity.touch_x
                        val padY = if (joyActive) joyY else activity.touch_y
                        val padBtn = joyBtn || activity.touch_force > 0.0
                        val padCap = padBtn || padX != 0.0 || padY != 0.0
                        viveBuffer.clear(); viveBuffer.putTag("ive")
                        viveBuffer.putBools(system, gripOn, select, trigBtn, padBtn, padCap)
                        viveBuffer.putDoubles(trig, padX, padY)
                        socket.send(DatagramPacket(viveBuffer.array(), viveBuffer.position(), address, portInt))
                    }
                    "frame" -> {
                        // frame: every source has click + touch, touch always follows the click
                        val yUp = activity.yUp; val aDown = activity.aDown; val xLeft = activity.xLeft; val bRight = activity.bRight
                        val bumper = activity.bumper
                        frameBuffer.clear(); frameBuffer.putTag("ifm")
                        frameBuffer.putBools(
                            yUp, yUp, aDown, aDown, xLeft, xLeft, bRight, bRight,
                            select, select, bumper, bumper, system, system,
                            trigBtn, trigCap, gripOn, gripOn, joyBtn, joyCap
                        )
                        frameBuffer.putDoubles(trig, gripVal, joyX, joyY)
                        socket.send(DatagramPacket(frameBuffer.array(), frameBuffer.position(), address, portInt))
                    }
                    else -> {
                        // index idk
                        val touchCap = activity.touch_x != 0.0 || activity.touch_y != 0.0 || activity.touch_force > CAP_AT
                        indexBuffer.clear(); indexBuffer.putTag("idx")
                        indexBuffer.putBools(
                            a, b, system, joyBtn, trigBtn,
                            a, b, system, joyCap, trigCap, touchCap, gripOn
                        )
                        indexBuffer.putDoubles(joyX, joyY, activity.touch_x, activity.touch_y, trig, activity.touch_force, gripVal, gripVal)
                        socket.send(DatagramPacket(indexBuffer.array(), indexBuffer.position(), address, portInt))
                    }
                }

                skeletalBuffer.clear(); skeletalBuffer.putTag("skl")
                val isHandActive = activity.joy_x != 0.0 || activity.joy_y != 0.0 || activity.joy_btn ||
                        activity.touch_x != 0.0 || activity.touch_y != 0.0 || activity.touch_force != 0.0
                activity.flexions[0] = if (isHandActive) 1.0 else 0.0
                activity.flexions[4] = if (activity.trigger > 0.1) 1.0 else 0.0
                if (activity.grip) { activity.flexions[8] = 1.0; activity.flexions[12] = 1.0; activity.flexions[16] = 1.0 }
                else { activity.flexions[8] = if (activity.middle > 0.0) 1.0 else 0.0; activity.flexions[12] = if (activity.ring > 0.0) 1.0 else 0.0; activity.flexions[16] = if (activity.pinky > 0.0) 1.0 else 0.0 }
                for (f in activity.flexions) skeletalBuffer.putDouble(f)
                for (s2 in activity.splays) skeletalBuffer.putDouble(s2)
                socket.send(DatagramPacket(skeletalBuffer.array(), skeletalBuffer.position(), address, portInt))
                Thread.sleep(1)
            }
            socket.close()
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        if (showBrowser) {
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { ctx ->
                    WebView(ctx).apply {
                        layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
                        webViewClient = object : WebViewClient() {
                            override fun onReceivedSslError(view: WebView, handler: android.webkit.SslErrorHandler, error: android.net.http.SslError) {
                                handler.proceed()
                            }
                        }
                        settings.javaScriptEnabled = true; settings.domStorageEnabled = true
                        loadUrl(browserUrl)
                    }
                }
            )
        }

        if (!showBrowser) {
            SuperButton(id = "a", label = "A", isActive = activity.a, onToggle = { activity.a = it }, defaultX = 50f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "b", label = "B", isActive = activity.b, onToggle = { activity.b = it }, defaultX = 150f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "system", label = "SYS", isActive = activity.system, onToggle = { activity.system = it }, defaultX = 250f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "grip(hold)", label = "GRIP\nHOLD", isActive = activity.grip, onToggle = { activity.grip = it }, defaultX = 250f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "grip(toggle)", label = "GRIP\nTOGGLE", isActive = activity.grip, onToggle = { activity.grip = it }, defaultX = 250f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "trigger", label = "TRIGGER", isActive = (activity.trigger != 0.0), onToggle = { isActive -> activity.trigger = if (isActive) 1.0 else 0.0 }, defaultX = 250f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperJoystick(id = "joystick", prefs = prefs, activity = activity, onJoyInput = { x, y -> activity.joy_x = x; activity.joy_y = y })
            SuperButton(id = "joystick_btn(hold)", label = "JOY BTN\nHOLD", isActive = activity.joy_btn, onToggle = { activity.joy_btn = it }, defaultX = 50f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "joystick_btn(toggle)", label = "JOY BTN\nTOGGLE", isActive = activity.joy_btn, onToggle = { activity.joy_btn = it }, defaultX = 150f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperTouchpad(id = "touchpad", prefs = prefs, activity = activity, onTouchInput = { x, y -> activity.touch_x = x; activity.touch_y = y })
            SuperButton(id = "touchpad_btn", label = "TOUCH BTN", isActive = (activity.touch_force != 0.0), onToggle = { isActive -> activity.touch_force = if (isActive) 1.0 else 0.0 }, defaultX = 250f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "reset", label = "RESET", isActive = false, onToggle = { activity.resetSession() }, defaultX = 200f, defaultY = 200f, prefs = prefs, activity = activity)
            SuperButton(id = "pinky", label = "PINKY", isActive = (activity.pinky != 0.0), onToggle = { isActive -> activity.pinky = if (isActive) 1.0 else 0.0 }, defaultX = 250f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "ring", label = "RING", isActive = (activity.ring != 0.0), onToggle = { isActive -> activity.ring = if (isActive) 1.0 else 0.0 }, defaultX = 250f, defaultY = 100f, prefs = prefs, activity = activity)
            SuperButton(id = "middle", label = "MIDDLE", isActive = (activity.middle != 0.0), onToggle = { isActive -> activity.middle = if (isActive) 1.0 else 0.0 }, defaultX = 250f, defaultY = 100f, prefs = prefs, activity = activity)

            SuperButton(id = "select", label = "SELECT", isActive = activity.select, onToggle = { activity.select = it }, defaultX = 50f, defaultY = 200f, prefs = prefs, activity = activity)
            SuperButton(id = "bumper", label = "BUMPER", isActive = activity.bumper, onToggle = { activity.bumper = it }, defaultX = 150f, defaultY = 200f, prefs = prefs, activity = activity)

            SuperButton(id = "y_up", label = "Y/UP", isActive = activity.yUp, onToggle = { activity.yUp = it }, defaultX = 50f, defaultY = 300f, prefs = prefs, activity = activity)
            SuperButton(id = "a_down", label = "A/DOWN", isActive = activity.aDown, onToggle = { activity.aDown = it }, defaultX = 150f, defaultY = 300f, prefs = prefs, activity = activity)
            SuperButton(id = "x_left", label = "X/LEFT", isActive = activity.xLeft, onToggle = { activity.xLeft = it }, defaultX = 250f, defaultY = 300f, prefs = prefs, activity = activity)
            SuperButton(id = "b_right", label = "B/RIGHT", isActive = activity.bRight, onToggle = { activity.bRight = it }, defaultX = 350f, defaultY = 300f, prefs = prefs, activity = activity)
        }

        val uriHandler = LocalUriHandler.current
        val showNav = when (showNavState) { "horizontal" -> isLandscape; "vertical" -> !isLandscape; else -> true }
        if (showNav) {
            if (isLandscape) {
                Column(modifier = Modifier.fillMaxHeight().width(32.dp).background(Color.Black.copy(alpha = 0.55f)).padding(4.dp), verticalArrangement = Arrangement.Top, horizontalAlignment = Alignment.CenterHorizontally) {
                    IconTextButton(label = "⚙", modifier = Modifier.fillMaxWidth().height(64.dp), onClick = { settingsExpanded = !settingsExpanded })
                    Spacer(modifier = Modifier.height(4.dp))
                    RotatedResetButton(modifier = Modifier.weight(1f).fillMaxWidth(), onClick = { activity.resetSession() })
                }
            } else {
                Row(modifier = Modifier.fillMaxWidth().wrapContentHeight().background(Color.Black.copy(alpha = 0.55f)).padding(4.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconTextButton(label = "⚙", modifier = Modifier.size(64.dp), onClick = { settingsExpanded = !settingsExpanded })
                    Spacer(modifier = Modifier.width(4.dp))
                    Button(onClick = { activity.resetSession() }, modifier = Modifier.weight(1f).height(64.dp), colors = ButtonDefaults.buttonColors(containerColor = Color.Gray), contentPadding = PaddingValues(0.dp), shape = MaterialTheme.shapes.small) {
                        Text("↺", fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        if (settingsExpanded) {
            Box(modifier = Modifier.fillMaxSize().padding(top = 44.dp)) {
                Card(modifier = Modifier.wrapContentSize().padding(8.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A2E).copy(alpha = 0.95f)), elevation = CardDefaults.cardElevation(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp).verticalScroll(rememberScrollState()).widthIn(min = 260.dp, max = 340.dp)) {
                        Text("Settings", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 16.sp, modifier = Modifier.padding(bottom = 12.dp))

                        val displayMetrics = LocalContext.current.resources.displayMetrics
                        val widthPx = displayMetrics.widthPixels; val heightPx = displayMetrics.heightPixels
                        val density = displayMetrics.density
                        Text("Resolution", color = Color.Gray, fontSize = 11.sp)
                        Text("${widthPx} × ${heightPx} px  (${(widthPx/density).toInt()} × ${(heightPx/density).toInt()} dp)", color = Color.White, fontSize = 12.sp, modifier = Modifier.padding(bottom = 10.dp))

                        Text("Host IP", color = Color.Gray, fontSize = 11.sp)
                        OutlinedTextField(value = ipAddress, onValueChange = { ipAddress = it }, singleLine = true, colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray), modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp))

                        Text("Port", color = Color.Gray, fontSize = 11.sp)
                        OutlinedTextField(value = port, onValueChange = { if (it.isEmpty() || it.all { c -> c.isDigit() }) port = it }, singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray), modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp))

                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                            Checkbox(checked = isVertical, onCheckedChange = { isVertical = it }, colors = CheckboxDefaults.colors(checkedColor = Color(0xFF5C6BC0)))
                            Text(if (isVertical) "Vertical (portrait)" else "Horizontal (landscape)", color = Color.White, fontSize = 13.sp)
                        }
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                            Checkbox(checked = isStreaming, onCheckedChange = { isStreaming = it }, colors = CheckboxDefaults.colors(checkedColor = Color(0xFF43A047), uncheckedColor = Color.Gray))
                            Text(if (isStreaming) "Streaming ON" else "Streaming OFF", color = if (isStreaming) Color(0xFF81C784) else Color.White, fontSize = 13.sp)
                        }
//                      slop plz ignore-----------------------------
//                      qr sync test, the idea is for all devices to look at the same qr, click sync and they all know where they are in relation,
//                      a more modern approach will be with point cloud matching, need more research
//                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
//                            Checkbox(checked = useQrState, onCheckedChange = { useQrState = it }, colors = CheckboxDefaults.colors(checkedColor = Color(0xFF5C6BC0)))
//                            Text(if (useQrState) "Origin: QR code" else "Origin: current pose", color = Color.White, fontSize = 13.sp)
//                        }
                        if (useQrState) {
                            Text("QR Marker Size (m, edge-to-edge)", color = Color.Gray, fontSize = 11.sp)
                            OutlinedTextField(
                                value = qrSizeStr,
                                onValueChange = { nv -> if (nv.isEmpty() || nv.matches(Regex("\\d*\\.?\\d*"))) qrSizeStr = nv },
                                singleLine = true,
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray),
                                modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp)
                            )
                        }

                        Text("Controller Type", color = Color.Gray, fontSize = 11.sp, modifier = Modifier.padding(bottom = 4.dp))
                        var conTypeDropdownExpanded by remember { mutableStateOf(false) }
                        ExposedDropdownMenuBox(expanded = conTypeDropdownExpanded, onExpandedChange = { conTypeDropdownExpanded = it }) {
                            OutlinedTextField(value = conTypeState, onValueChange = {}, readOnly = true, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = conTypeDropdownExpanded) }, colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray), modifier = Modifier.menuAnchor().fillMaxWidth())
                            ExposedDropdownMenu(expanded = conTypeDropdownExpanded, onDismissRequest = { conTypeDropdownExpanded = false }, containerColor = Color(0xFF1A1A2E)) {
                                controllerTypes.forEach { option -> DropdownMenuItem(text = { Text(option, color = Color.White) }, onClick = { conTypeState = option; conTypeDropdownExpanded = false }) }
                            }
                        }
                        Spacer(modifier = Modifier.height(10.dp))

                        PresetLayoutComboBox(
                            prefs = prefs,
                            activity = activity,
                            browserUrl = browserUrl,
                            onOpenBrowser = {
                                showBrowser = true
                                val editor = prefs.edit()
                                allButtonIds.forEach { id -> editor.putBoolean("${id}_isDisabled", true) }
                                editor.apply()
                                activity.layoutRefreshTrigger++
                            },
                            onCloseBrowser = { showBrowser = false },

                            onSelectConType = { conTypeState = it }
                        )

                        val flipDensity = LocalDensity.current
                        val flipScreenWidthPx = with(flipDensity) { configuration.screenWidthDp.dp.toPx() }
                        OutlinedButton(onClick = { flipLayoutHorizontal(prefs, flipScreenWidthPx, flipDensity); activity.layoutRefreshTrigger++ }, modifier = Modifier.fillMaxWidth(), colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White), border = BorderStroke(1.dp, Color.Gray)) {
                            Text("⇆  Flip Layout")
                        }
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                            Checkbox(checked = activity.InEdit, onCheckedChange = { activity.InEdit = it }, colors = CheckboxDefaults.colors(checkedColor = Color(0xFF43A047), uncheckedColor = Color.Gray))
                            Text(text = if (activity.InEdit) "Editing" else "Not Editing", color = if (activity.InEdit) Color(0xFF81C784) else Color.White, fontSize = 13.sp)
                        }

                        Text("Vertical Pitch Offset(default -90.0)", color = Color.Gray, fontSize = 11.sp)
                        OutlinedTextField(value = pitchOffset.toString(), onValueChange = { nv -> if (nv.isEmpty() || nv == "-" || nv.matches(Regex("-?\\d*\\.?\\d*"))) pitchOffset = nv.toDoubleOrNull() ?: pitchOffset }, singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text), colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray), modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp))

                        Text("Browser URL", color = Color.Gray, fontSize = 11.sp)
                        OutlinedTextField(value = browserUrl, onValueChange = { browserUrl = it }, singleLine = true, colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray), modifier = Modifier.fillMaxWidth().padding(top = 4.dp, bottom = 10.dp))

                        Text("Volume Up Action", color = Color.Gray, fontSize = 11.sp, modifier = Modifier.padding(bottom = 4.dp))
                        ExposedDropdownMenuBox(expanded = volUpDropdownExpanded, onExpandedChange = { volUpDropdownExpanded = it }) {
                            OutlinedTextField(value = volUpState.label, onValueChange = {}, readOnly = true, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = volUpDropdownExpanded) }, colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray), modifier = Modifier.menuAnchor().fillMaxWidth())
                            ExposedDropdownMenu(expanded = volUpDropdownExpanded, onDismissRequest = { volUpDropdownExpanded = false }, containerColor = Color(0xFF1A1A2E)) {
                                HardwareAction.entries.forEach { action -> DropdownMenuItem(text = { Text(action.label, color = Color.White) }, onClick = { volUpState = action; activity.volUpAction = action; activity.sharedPrefs.edit().putString("volUp", action.name).apply(); volUpDropdownExpanded = false }) }
                            }
                        }

                        Text("Volume Down Action", color = Color.Gray, fontSize = 11.sp, modifier = Modifier.padding(bottom = 4.dp))
                        ExposedDropdownMenuBox(expanded = volDownDropdownExpanded, onExpandedChange = { volDownDropdownExpanded = it }) {
                            OutlinedTextField(value = volDownState.label, onValueChange = {}, readOnly = true, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = volDownDropdownExpanded) }, colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray), modifier = Modifier.menuAnchor().fillMaxWidth())
                            ExposedDropdownMenu(expanded = volDownDropdownExpanded, onDismissRequest = { volDownDropdownExpanded = false }, containerColor = Color(0xFF1A1A2E)) {
                                HardwareAction.entries.forEach { action -> DropdownMenuItem(text = { Text(action.label, color = Color.White) }, onClick = { volDownState = action; activity.volDownAction = action; activity.sharedPrefs.edit().putString("volDown", action.name).apply(); volDownDropdownExpanded = false }) }
                            }
                        }

                        Text("Show Nav Bar", color = Color.Gray, fontSize = 11.sp, modifier = Modifier.padding(bottom = 4.dp))
                        var showNavDropdownExpanded by remember { mutableStateOf(false) }
                        ExposedDropdownMenuBox(expanded = showNavDropdownExpanded, onExpandedChange = { showNavDropdownExpanded = it }) {
                            OutlinedTextField(value = showNavState, onValueChange = {}, readOnly = true, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = showNavDropdownExpanded) }, colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray), modifier = Modifier.menuAnchor().fillMaxWidth())
                            ExposedDropdownMenu(expanded = showNavDropdownExpanded, onDismissRequest = { showNavDropdownExpanded = false }, containerColor = Color(0xFF1A1A2E)) {
                                listOf("both", "horizontal", "vertical").forEach { option ->
                                    DropdownMenuItem(text = { Text(option, color = Color.White) }, onClick = {
                                        showNavState = option
                                        val navWillHide = when (option) { "horizontal" -> !isLandscape; "vertical" -> isLandscape; else -> false }
                                        if (navWillHide) { settingsExpanded = false; if (showNavHiddenToast) Toast.makeText(context, "Navbar is hidden, rotate your phone! (Toast can be disable in settings)", Toast.LENGTH_LONG).show() }
                                        showNavDropdownExpanded = false
                                    })
                                }
                            }
                        }
                        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                            Checkbox(checked = !showNavHiddenToast, onCheckedChange = { showNavHiddenToast = !it }, colors = CheckboxDefaults.colors(checkedColor = Color(0xFF5C6BC0), uncheckedColor = Color.Gray))
                            Text("disable orientation warning toast", color = Color.White, fontSize = 13.sp)
                        }

                        Text("Made By: DaniXmir", color = Color.White, fontSize = 24.sp, modifier = Modifier.padding(bottom = 4.dp))
                        GifButton()
                        Row {
                            Text(text = "youtube!", color = Color(0xFF5C6BC0), fontSize = 22.sp, textDecoration = TextDecoration.Underline, modifier = Modifier.clickable { uriHandler.openUri("https://www.youtube.com/@danixmir106") }.padding(vertical = 4.dp))
                            Text("   ", color = Color.White, fontSize = 24.sp)
                            Text(text = "github!", color = Color(0xFF5C6BC0), fontSize = 22.sp, textDecoration = TextDecoration.Underline, modifier = Modifier.clickable { uriHandler.openUri("https://github.com/DaniXmir/GlassVr") }.padding(vertical = 4.dp))
                            Text("   ", color = Color.White, fontSize = 24.sp)
                            Text(text = "discord!", color = Color(0xFF5C6BC0), fontSize = 22.sp, textDecoration = TextDecoration.Underline, modifier = Modifier.clickable { uriHandler.openUri("https://discord.com/invite/jyvWdKBpPj") }.padding(vertical = 4.dp))
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun IconTextButton(label: String, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Button(onClick = onClick, modifier = modifier, colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF37474F)), contentPadding = PaddingValues(0.dp)) { Text(label, fontSize = 16.sp) }
}
@Composable
fun RotatedResetButton(modifier: Modifier = Modifier, onClick: () -> Unit) {
    Button(onClick = onClick, modifier = modifier, colors = ButtonDefaults.buttonColors(containerColor = Color.Gray), contentPadding = PaddingValues(0.dp), shape = MaterialTheme.shapes.small) { Text("↺", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color.White) }
}
@Composable
fun GifButton() {
    val context = LocalContext.current
    AsyncImage(model = ImageRequest.Builder(context).data(R.drawable.fix_anim).decoderFactory(GifDecoder.Factory()).build(), contentDescription = "Alert Button",
        modifier = Modifier.size(200.dp).clickable {
            val alertContext = ContextThemeWrapper(context, android.R.style.Theme_Dialog)
            AlertDialog.Builder(alertContext).setTitle(";P").setMessage("OUCH!").setPositiveButton("ok") { d, _ -> d.dismiss() }.create().show()
        })
}
@Composable
fun Gif() {
    AsyncImage(model = ImageRequest.Builder(LocalContext.current).data(R.drawable.fix_anim).decoderFactory(GifDecoder.Factory()).build(), contentDescription = null, modifier = Modifier.size(200.dp))
}

// centered = the region only decides where the joystick sits, the circle is centered inside it (used by the vive layout)
data class LayoutRegion(val startPct: Pair<Float, Float>, val endPct: Pair<Float, Float>, val isToggle: Boolean = false, val centered: Boolean = false)

val controllerTypes = listOf("index", "touch", "vive", "frame")

val allButtonIds = listOf("a", "b", "system", "grip(hold)", "grip(toggle)", "trigger", "joystick", "joystick_btn(hold)", "joystick_btn(toggle)", "touchpad", "touchpad_btn", "reset", "middle", "ring", "pinky",
    "select", "bumper", "y_up", "a_down", "x_left", "b_right")

// ids added with the controller types
val newButtonIds = listOf("select", "bumper", "y_up", "a_down", "x_left", "b_right")

// these never move between the index / touch / vive / frame layouts, mostly!
private val REGION_TRIGGER = LayoutRegion(0.0f to 0.1f, 0.9f to 0.3f)
private val REGION_RESET = LayoutRegion(0.9f to 0.1f, 1.0f to 0.2f)
private val REGION_SYSTEM = LayoutRegion(0.9f to 0.2f, 1.0f to 0.3f)
private val REGION_GRIP_HOLD = LayoutRegion(0.4f to 0.7f, 0.8f to 1.0f)
private val REGION_GRIP_TOGGLE = LayoutRegion(0.0f to 0.7f, 0.4f to 1.0f, isToggle = true)

val presetLayouts = mapOf(
    "none" to mapOf<String, LayoutRegion>(),
    "compact" to mapOf(
        "a" to LayoutRegion(0.0f to 0.3f, 0.3f to 0.5f), "b" to LayoutRegion(0.0f to 0.5f, 0.3f to 0.7f),
        "system" to LayoutRegion(0.0f to 0.0f, 0.0f to 0.2f), "grip(hold)" to LayoutRegion(0.0f to 0.0f, 0.0f to 0.0f),
        "grip(toggle)" to LayoutRegion(0.0f to 0.0f, 0.0f to 0.0f), "trigger" to LayoutRegion(0.0f to 0.0f, 0.0f to 0.0f),
        "joystick" to LayoutRegion(0.5f to 0.3f, 1.0f to 1.0f),
        "joystick_btn(toggle)" to LayoutRegion(0.0f to 0.0f, 0.0f to 0.0f, isToggle = true),
        "joystick_btn(hold)" to LayoutRegion(0.0f to 0.0f, 0.0f to 0.0f),
        "reset" to LayoutRegion(0.0f to 0.0f, 0.0f to 0.0f)
    ),
    // valve index (was "full"): a/b, joystick + click, touchpad + click
    "index" to mapOf(
        "b" to LayoutRegion(0.0f to 0.3f, 0.3f to 0.5f), "a" to LayoutRegion(0.0f to 0.5f, 0.3f to 0.7f),
        "system" to REGION_SYSTEM, "grip(hold)" to REGION_GRIP_HOLD,
        "grip(toggle)" to REGION_GRIP_TOGGLE, "trigger" to REGION_TRIGGER,
        "joystick" to LayoutRegion(0.5f to 0.3f, 1.0f to 1.0f),
        "joystick_btn(toggle)" to LayoutRegion(0.5f to 0.5f, 0.75f to 0.6f, isToggle = true),
        "joystick_btn(hold)" to LayoutRegion(0.75f to 0.5f, 1.0f to 0.6f),
        "reset" to REGION_RESET, "touchpad" to LayoutRegion(0.3f to 0.3f, 0.5f to 0.6f),
        "touchpad_btn" to LayoutRegion(0.3f to 0.6f, 0.5f to 0.7f)
    ),
    // oculus / meta touch: the index layout without the touchpad
    "touch" to mapOf(
        "b" to LayoutRegion(0.0f to 0.3f, 0.5f to 0.5f),
        "a" to LayoutRegion(0.0f to 0.5f, 0.5f to 0.7f),
        "system" to REGION_SYSTEM, "grip(hold)" to REGION_GRIP_HOLD,
        "grip(toggle)" to REGION_GRIP_TOGGLE, "trigger" to REGION_TRIGGER,
        "joystick" to LayoutRegion(0.5f to 0.3f, 1.0f to 1.0f),
        "joystick_btn(toggle)" to LayoutRegion(0.5f to 0.5f, 0.75f to 0.6f, isToggle = true),
        "joystick_btn(hold)" to LayoutRegion(0.75f to 0.5f, 1.0f to 0.6f),
        "reset" to REGION_RESET
    ),
    "touch(skeletal)" to mapOf(
        "a" to LayoutRegion(0.4f to 0.53f, 0.5f to 0.76f),
        "b" to LayoutRegion(0.4f to 0.3f, 0.5f to 0.53f),
        "middle" to LayoutRegion(0.0f to 0.3f, 0.4f to 0.53f),
        "ring" to LayoutRegion(0.0f to 0.53f, 0.4f to 0.76f),
        "pinky" to LayoutRegion(0.0f to 0.76f, 0.4f to 1.0f),
        "grip(toggle)" to LayoutRegion(0.4f to 0.76f, 0.8f to 1.0f, isToggle = true),
        "joystick" to LayoutRegion(0.5f to 0.3f, 1.0f to 1.0f),
        "joystick_btn(toggle)" to LayoutRegion(0.5f to 0.5f, 0.75f to 0.6f, isToggle = true),
        "joystick_btn(hold)" to LayoutRegion(0.75f to 0.5f, 1.0f to 0.6f),
        "trigger" to REGION_TRIGGER,
        "system" to REGION_SYSTEM,
        "reset" to REGION_RESET
    ),
    "vive" to mapOf(
        "system" to REGION_SYSTEM, "grip(hold)" to REGION_GRIP_HOLD,
        "grip(toggle)" to REGION_GRIP_TOGGLE, "trigger" to REGION_TRIGGER,
        "select" to LayoutRegion(0.3f to 0.3f, 0.7f to 0.4f),
        "joystick" to LayoutRegion(0.2f to 0.35f, 0.8f to 0.75f, centered = true),
        "joystick_btn(toggle)" to LayoutRegion(0.0f to 0.3f, 0.2f to 0.5f, isToggle = true), // toggle not working???
        "joystick_btn(hold)" to LayoutRegion(0.0f to 0.5f, 0.2f to 0.7f),
        "reset" to REGION_RESET
    ),
    "frame" to mapOf(
        "y_up" to LayoutRegion(0.125f to 0.4f, 0.375f to 0.5f),
        "x_left" to LayoutRegion(0.0f to 0.5f, 0.25f to 0.6f),
        "b_right" to LayoutRegion(0.25f to 0.5f, 0.5f to 0.6f),
        "a_down" to LayoutRegion(0.125f to 0.6f, 0.375f to 0.7f),
        "select" to LayoutRegion(0.8f to 0.7f, 1.0f to 0.8f), "bumper" to LayoutRegion(0.0f to 0.3f, 1.0f to 0.4f),
        "system" to REGION_SYSTEM, "grip(hold)" to REGION_GRIP_HOLD,
        "grip(toggle)" to REGION_GRIP_TOGGLE, "trigger" to REGION_TRIGGER,
        "joystick" to LayoutRegion(0.5f to 0.4f, 1.0f to 1.0f),
        "joystick_btn(toggle)" to LayoutRegion(0.5f to 0.61f, 0.75f to 0.7f, isToggle = true),
        "joystick_btn(hold)" to LayoutRegion(0.75f to 0.61f, 1.0f to 0.7f),
        "reset" to REGION_RESET
    )
)

fun flipLayoutHorizontal(prefs: android.content.SharedPreferences, screenWidthPx: Float, density: androidx.compose.ui.unit.Density) {
    val editor = prefs.edit()
    allButtonIds.forEach { id ->
        val x = prefs.getFloat("${id}_x", Float.MIN_VALUE); if (x == Float.MIN_VALUE) return@forEach
        val widthPx = when (id) {
            "joystick" -> with(density) { prefs.getFloat("${id}_size", 160f).dp.toPx() }
            "touchpad", "touchpad_btn" -> with(density) { prefs.getFloat("${id}_width", 120f).dp.toPx() }
            else -> with(density) { prefs.getFloat("${id}_width", 80f).dp.toPx() }
        }
        editor.putFloat("${id}_x", screenWidthPx - x - widthPx)
    }
    editor.apply()
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PresetLayoutComboBox(
    prefs: android.content.SharedPreferences,
    activity: MainActivity,
    browserUrl: String = "",
    onOpenBrowser: () -> Unit = {},
    onCloseBrowser: () -> Unit = {},
    onSelectConType: (String) -> Unit = {},
    mirror: Boolean = false
) {
    val configuration = LocalConfiguration.current
    val options = listOf("pass") + controllerTypes + listOf("touch(skeletal)", "browser", "none")
    var expanded by remember { mutableStateOf(false) }
    var selectedOption by remember { mutableStateOf("pass") }
    val density = LocalDensity.current
    val screenWidthPx = with(density) { configuration.screenWidthDp.dp.toPx() }
    val screenHeightPx = with(density) { configuration.screenHeightDp.dp.toPx() }

    Box(modifier = Modifier.padding(vertical = 8.dp)) {
        ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
            OutlinedTextField(modifier = Modifier.menuAnchor().fillMaxWidth(), readOnly = true, value = selectedOption, onValueChange = {},
                label = { Text("Preset Layout", color = Color.White) }, trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                colors = OutlinedTextFieldDefaults.colors(focusedTextColor = Color.White, unfocusedTextColor = Color.White, focusedBorderColor = Color(0xFF0288D1), unfocusedBorderColor = Color.Gray))
            ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                options.forEach { option ->
                    DropdownMenuItem(text = { Text(option) }, onClick = {
                        selectedOption = option; expanded = false

                        if (option == "browser") onOpenBrowser() else onCloseBrowser()

                        // index / touch / vive / frame layouts are tied to a controller type
                        if (option in controllerTypes) onSelectConType(option)

                        if (option != "browser" && option != "none" && option != "pass") {
                            val activeRegions = presetLayouts[option] ?: emptyMap()
                            val editor = prefs.edit()
                            allButtonIds.forEach { id ->
                                val region = activeRegions[id]; val shouldEnable = region != null
                                editor.putBoolean("${id}_isDisabled", !shouldEnable)
                                if (shouldEnable && region != null) {
                                    val startX = region.startPct.first; val startY = region.startPct.second
                                    val endX = region.endPct.first; val endY = region.endPct.second
                                    val width = (endX - startX).coerceAtLeast(0f) * screenWidthPx
                                    val height = (endY - startY).coerceAtLeast(0f) * screenHeightPx
                                    var x = if (mirror) screenWidthPx - (endX * screenWidthPx) else startX * screenWidthPx
                                    var y = startY * screenHeightPx
                                    if (region.centered) {
                                        val side = minOf(width, height)
                                        x += (width - side) / 2f
                                        y += (height - side) / 2f
                                    }
                                    editor.putFloat("${id}_x", x); editor.putFloat("${id}_y", y)
                                    editor.putFloat("${id}_width", with(density) { width.toDp().value })
                                    editor.putFloat("${id}_height", with(density) { height.toDp().value })
                                    if (id != "joystick" && id != "joystick_btn(hold)" && id != "joystick_btn(toggle)" && id != "touchpad" && id != "touchpad_btn")
                                        editor.putBoolean("${id}_isToggle", region.isToggle)
                                    if (id == "joystick") editor.putFloat("${id}_size", minOf(with(density) { width.toDp().value }, with(density) { height.toDp().value }))
                                }
                            }
                            editor.apply(); activity.layoutRefreshTrigger++
                        }

                        if (option == "none") {
                            val editor = prefs.edit()
                            allButtonIds.forEach { id -> editor.putBoolean("${id}_isDisabled", true) }
                            editor.apply(); activity.layoutRefreshTrigger++
                        }
                    })
                }
            }
        }
    }
}

@Composable
fun SuperButton(id: String, label: String, isActive: Boolean, onToggle: (Boolean) -> Unit, defaultX: Float, defaultY: Float, defaultWidth: Float = 80f, defaultHeight: Float = 80f, defaultIsToggle: Boolean = false, prefs: android.content.SharedPreferences, activity: MainActivity) {
    val isEditMode = activity.InEdit; val refreshTrigger = activity.layoutRefreshTrigger
    val currentOnToggle by rememberUpdatedState(onToggle)
    var isLocallyActive by remember { mutableStateOf(isActive) }
    var offsetX by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_x", defaultX)) }
    var offsetY by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_y", defaultY)) }
    var widthDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_width", defaultWidth)) }
    var heightDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_height", defaultHeight)) }
    var isToggleMode by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getBoolean("${id}_isToggle", defaultIsToggle)) }
    var isDisabled by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getBoolean("${id}_isDisabled", false)) }
    if (isDisabled && !isEditMode) return
    var isDragging by remember { mutableStateOf(false) }; var isResizing by remember { mutableStateOf(false) }
    Box(modifier = Modifier.offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }.requiredSize(width = widthDp.dp, height = heightDp.dp).alpha(if (isDisabled && isEditMode) 0.4f else 1f).background(if (isLocallyActive) Color.Red else Color.Gray, RoundedCornerShape(12.dp)).pointerInput(isEditMode, isToggleMode) {
        if (isEditMode) { detectDragGestures(onDragStart = { isDragging = true }, onDragEnd = { isDragging = false; prefs.edit().putFloat("${id}_x", offsetX).putFloat("${id}_y", offsetY).apply() }, onDrag = { change, dragAmount -> change.consume(); offsetX += dragAmount.x; offsetY += dragAmount.y }) }
        else { if (isToggleMode) detectTapGestures(onTap = { isLocallyActive = !isLocallyActive; currentOnToggle(isLocallyActive) }) else detectTapGestures(onPress = { isLocallyActive = true; currentOnToggle(true); tryAwaitRelease(); isLocallyActive = false; currentOnToggle(false) }) }
    }, contentAlignment = Alignment.Center) {
        if (isEditMode && (isDragging || isResizing)) {
            val cfg = LocalConfiguration.current; val d = LocalDensity.current
            val swpx = with(d) { cfg.screenWidthDp.dp.toPx() }; val shpx = with(d) { cfg.screenHeightDp.dp.toPx() }
            val wpx = with(d) { widthDp.dp.toPx() }; val hpx = with(d) { heightDp.dp.toPx() }
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text("X:${offsetX.roundToInt()} Y:${offsetY.roundToInt()}", color = Color.Green, fontSize = 10.sp, lineHeight = 11.sp)
                Text("W:${widthDp.roundToInt()} H:${heightDp.roundToInt()}", color = Color.Cyan, fontSize = 10.sp, lineHeight = 11.sp)
                Text("S:${"%.2f".format(offsetX/swpx)},${"%.2f".format(offsetY/shpx)}", color = Color.Yellow, fontSize = 10.sp, lineHeight = 11.sp)
                Text("E:${"%.2f".format((offsetX+wpx)/swpx)},${"%.2f".format((offsetY+hpx)/shpx)}", color = Color.Yellow, fontSize = 10.sp, lineHeight = 11.sp)
            }
        } else { Text(label, color = Color.White, fontSize = (minOf(widthDp, heightDp) * 0.25f).sp) }
        if (isEditMode) {
            Box(modifier = Modifier.align(Alignment.TopStart).padding(4.dp).background(Color(0x88000000), RoundedCornerShape(4.dp)).pointerInput(Unit) { detectTapGestures(onTap = { isDisabled = !isDisabled; prefs.edit().putBoolean("${id}_isDisabled", isDisabled).apply() }) }.padding(horizontal = 6.dp, vertical = 2.dp)) { Text(if (isDisabled) "HIDDEN" else "VISIBLE", color = if (isDisabled) Color(0xFFEF5350) else Color(0xFF66BB6A), fontSize = 9.sp, fontWeight = FontWeight.Bold) }
            Box(modifier = Modifier.align(Alignment.TopEnd).padding(4.dp).background(Color(0x88000000), RoundedCornerShape(4.dp)).pointerInput(Unit) { detectTapGestures(onTap = { isToggleMode = !isToggleMode; prefs.edit().putBoolean("${id}_isToggle", isToggleMode).apply() }) }.padding(horizontal = 6.dp, vertical = 2.dp)) { Text(if (isToggleMode) "TOGGLE" else "HOLD", color = if (isToggleMode) Color(0xFF4DB6AC) else Color(0xFFFF8A65), fontSize = 9.sp, fontWeight = FontWeight.Bold) }
            Box(modifier = Modifier.size(24.dp).align(Alignment.BottomEnd).background(Color(0x88FFEB3B), RoundedCornerShape(topStart = 8.dp, bottomEnd = 12.dp)).pointerInput(Unit) { detectDragGestures(onDragStart = { isResizing = true }, onDragEnd = { isResizing = false; prefs.edit().putFloat("${id}_width", widthDp).putFloat("${id}_height", heightDp).apply() }, onDrag = { change, dragAmount -> change.consume(); widthDp = (widthDp + dragAmount.x).coerceAtLeast(50f); heightDp = (heightDp + dragAmount.y).coerceAtLeast(50f) }) }) { Text("⤡", color = Color.Black, fontSize = 10.sp, modifier = Modifier.align(Alignment.Center)) }
        }
    }
}

@Composable
fun SuperJoystick(id: String, prefs: android.content.SharedPreferences, activity: MainActivity, onJoyInput: (Double, Double) -> Unit) {
    val isEditMode = activity.InEdit; val refreshTrigger = activity.layoutRefreshTrigger
    var offsetX by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_x", 0f)) }
    var offsetY by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_y", 0f)) }
    var sizeDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_size", 160f)) }
    var isDisabled by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getBoolean("${id}_isDisabled", false)) }
    var joystickOffset by remember { mutableStateOf(Offset.Zero) }
    val maxRadiusPx = (sizeDp / 2) * LocalDensity.current.density
    if (isDisabled && !isEditMode) return
    Box(modifier = Modifier.offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }.size(sizeDp.dp).alpha(if (isDisabled && isEditMode) 0.4f else 1f).background(Color.DarkGray.copy(alpha = 0.6f), CircleShape).pointerInput(isEditMode) {
        if (isEditMode) detectDragGestures { change, dragAmount -> change.consume(); offsetX += dragAmount.x; offsetY += dragAmount.y; prefs.edit().putFloat("${id}_x", offsetX).putFloat("${id}_y", offsetY).apply() }
        else detectDragGestures(onDragEnd = { joystickOffset = Offset.Zero; onJoyInput(0.0, 0.0) }, onDragCancel = { joystickOffset = Offset.Zero; onJoyInput(0.0, 0.0) }, onDrag = { change, dragAmount -> change.consume(); val newOffset = joystickOffset + dragAmount; val dist = newOffset.getDistance(); joystickOffset = if (dist <= maxRadiusPx) newOffset else newOffset / dist * maxRadiusPx; onJoyInput((joystickOffset.x / maxRadiusPx).toDouble(), -(joystickOffset.y / maxRadiusPx).toDouble()) })
    }, contentAlignment = Alignment.Center) {
        Box(modifier = Modifier.offset { IntOffset(joystickOffset.x.roundToInt(), joystickOffset.y.roundToInt()) }.size((sizeDp / 2).dp).background(Color(0xFF78909C), CircleShape))
        if (isEditMode) {
            Box(modifier = Modifier.align(Alignment.TopStart).padding(4.dp).background(Color(0x88000000), RoundedCornerShape(4.dp)).pointerInput(Unit) { detectTapGestures(onTap = { isDisabled = !isDisabled; prefs.edit().putBoolean("${id}_isDisabled", isDisabled).apply() }) }.padding(4.dp)) { Text(if (isDisabled) "HIDDEN" else "VISIBLE", color = Color.White, fontSize = 9.sp) }
            Box(modifier = Modifier.size(24.dp).align(Alignment.BottomEnd).background(Color(0x88FFEB3B), CircleShape).pointerInput(Unit) { detectDragGestures(onDragEnd = { prefs.edit().putFloat("${id}_size", sizeDp).apply() }, onDrag = { change, dragAmount -> change.consume(); sizeDp = (sizeDp + (dragAmount.x + dragAmount.y) / 2).coerceIn(100f, 300f) }) }) { Text("⤡", color = Color.Black, fontSize = 10.sp, modifier = Modifier.align(Alignment.Center)) }
        }
    }
}

@Composable
fun SuperTouchpad(id: String, prefs: android.content.SharedPreferences, activity: MainActivity, onTouchInput: (Double, Double) -> Unit) {
    val isEditMode = activity.InEdit; val refreshTrigger = activity.layoutRefreshTrigger
    var offsetX by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_x", 0f)) }
    var offsetY by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_y", 0f)) }
    var widthDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_width", 120f)) }
    var heightDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_height", 220f)) }
    var isDisabled by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getBoolean("${id}_isDisabled", false)) }
    var isTouching by remember { mutableStateOf(false) }
    if (isDisabled && !isEditMode) return
    Box(modifier = Modifier.offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }.size(width = widthDp.dp, height = heightDp.dp).alpha(if (isDisabled && isEditMode) 0.4f else 1f).background(if (isTouching) Color(0xFF455A64) else Color(0xFF263238), RoundedCornerShape(16.dp)).pointerInput(isEditMode) {
        if (isEditMode) detectDragGestures { change, dragAmount -> change.consume(); offsetX += dragAmount.x; offsetY += dragAmount.y; prefs.edit().putFloat("${id}_x", offsetX).putFloat("${id}_y", offsetY).apply() }
        else awaitPointerEventScope { while (true) { val event = awaitPointerEvent(); val pointer = event.changes.firstOrNull(); if (pointer != null && pointer.pressed) { isTouching = true; val s = size; val normX = ((pointer.position.x / s.width) * 2f - 1f).toDouble().coerceIn(-1.0, 1.0); val normY = -((pointer.position.y / s.height) * 2f - 1f).toDouble().coerceIn(-1.0, 1.0); onTouchInput(normX, normY); pointer.consume() } else { isTouching = false; onTouchInput(0.0, 0.0) } } }
    }, contentAlignment = Alignment.Center) {
        if (!isEditMode) Text("TOUCHPAD", color = Color.Gray, fontSize = 11.sp)
        if (isEditMode) {
            Box(modifier = Modifier.align(Alignment.TopStart).padding(4.dp).background(Color(0x88000000), RoundedCornerShape(4.dp)).pointerInput(Unit) { detectTapGestures(onTap = { isDisabled = !isDisabled; prefs.edit().putBoolean("${id}_isDisabled", isDisabled).apply() }) }.padding(4.dp)) { Text(if (isDisabled) "HIDDEN" else "VISIBLE", color = Color.White, fontSize = 9.sp) }
            Box(modifier = Modifier.size(24.dp).align(Alignment.BottomEnd).background(Color(0x88FFEB3B), RoundedCornerShape(4.dp)).pointerInput(Unit) { detectDragGestures(onDragEnd = { prefs.edit().putFloat("${id}_width", widthDp).putFloat("${id}_height", heightDp).apply() }, onDrag = { change, dragAmount -> change.consume(); widthDp = (widthDp + dragAmount.x).coerceAtLeast(50f); heightDp = (heightDp + dragAmount.y).coerceAtLeast(50f) }) }) { Text("⤡", color = Color.Black, fontSize = 10.sp, modifier = Modifier.align(Alignment.Center)) }
        }
    }
}

// will clean up if ill make an iphone version!
//;P