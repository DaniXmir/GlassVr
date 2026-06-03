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
import androidx.compose.foundation.clickable
import android.view.KeyEvent

import android.widget.Toast
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable

import androidx.compose.foundation.gestures.detectDragGestures
import kotlin.math.roundToInt

import android.app.AlertDialog
import android.view.ContextThemeWrapper

import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType

class MainActivity : ComponentActivity() {
    var InEdit by mutableStateOf(false)
    var layoutRefreshTrigger by mutableStateOf(0)

    val arSessionState = mutableStateOf<Session?>(null)
    lateinit var glSurfaceView: GLSurfaceView
    var renderer: ArRenderer? = null

    @Volatile var isVertical = false
    @Volatile var sendResetPacket = false
    @Volatile var resetFramesRemaining = 0

    //pos-rot
    @Volatile var latestTx = 0.0
    @Volatile var latestTy = 0.0
    @Volatile var latestTz = 0.0
    @Volatile var latestQw = 1.0
    @Volatile var latestQx = 0.0
    @Volatile var latestQy = 0.0
    @Volatile var latestQz = 0.0
    @Volatile var poseReady = false

    //offsets
    @Volatile var PitchOffset = -90.0

    //input (valve index controllers have a crazy level of configurability)
    @Volatile var a = false
    @Volatile var a_cap = false
    @Volatile var b = false
    @Volatile var b_cap = false
    @Volatile var system = false
    @Volatile var system_cap = false
    @Volatile var touch_cap = false
    @Volatile var grip_cap = false
    @Volatile var joy_x = 0.0
    @Volatile var joy_y = 0.0
    @Volatile var joy_btn = false
    @Volatile var joy_cap = false
    @Volatile var touch_x = 0.0
    @Volatile var touch_y = 0.0
    @Volatile var touch_force = 0.0
    @Volatile var trigger = 0.0
    @Volatile var trigger_btn = false
    @Volatile var trigger_cap = false
    @Volatile var grip_pull = 0.0
    @Volatile var grip_force = 0.0

    //skeletal
    @Volatile var flexions = DoubleArray(20) { 0.0 }
    @Volatile var splays = DoubleArray(5) { 0.0 }

    //actions (will change!)
    @Volatile var volUpAction = HardwareAction.NONE
    @Volatile var volDownAction = HardwareAction.NONE
    lateinit var sharedPrefs: android.content.SharedPreferences

    //physical buttons-----------------------------------------------------------------------------------
//    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
//        when (keyCode) {
//            KeyEvent.KEYCODE_VOLUME_DOWN -> {
//                grip_pull = 1.0
//                grip_cap = true
//                return true
//            }
//            KeyEvent.KEYCODE_VOLUME_UP -> {
//                trigger = 1.0
//                trigger_btn = true
//                return true
//            }
//            //cant use power :(
////            KeyEvent.KEYCODE_POWER -> {
////                grip_pull = 1.0
////                grip_cap = true
////                return true
////            }
//        }
//        return super.onKeyDown(keyCode, event)
//    }
//
//    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
//        when (keyCode) {
//            KeyEvent.KEYCODE_VOLUME_DOWN -> {
//                grip_pull = 0.0
//                grip_cap = false
//                return true
//            }
//            KeyEvent.KEYCODE_VOLUME_UP -> {
//                trigger = 0.0
//                trigger_btn = false
//                return true
//            }
//            //cant use power :(
////            KeyEvent.KEYCODE_POWER -> {
////                grip_pull = 0.0
////                grip_cap = false
////                return true
////            }
//        }
//        return super.onKeyUp(keyCode, event)
//    }

    //(will change!)
    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        val action = when (keyCode) {
            KeyEvent.KEYCODE_VOLUME_UP -> volUpAction
            KeyEvent.KEYCODE_VOLUME_DOWN -> volDownAction
            else -> return super.onKeyDown(keyCode, event)
        }

        when (action) {
            HardwareAction.TRIGGER -> { trigger = 1.0;}
            HardwareAction.GRIP_HOLD -> { grip_force = 1.0;}
            HardwareAction.GRIP_TOGGLE -> {
                if (event?.repeatCount == 0) {
                    val newState = if (grip_force > 0.5) 0.0 else 1.0
                    grip_force = newState
                }
            }
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
            HardwareAction.TRIGGER -> { trigger = 0.0;}
            HardwareAction.GRIP_HOLD -> { grip_force = 0.0;}
            HardwareAction.GRIP_TOGGLE -> {}
            HardwareAction.NONE -> return super.onKeyUp(keyCode, event)
        }
        return true
    }

    //physical buttons-----------------------------------------------------------------------------------

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge(
            navigationBarStyle = SystemBarStyle.dark(scrim = Color.Black.toArgb())
        )
        super.onCreate(savedInstanceState)
        setContent {
            val context = LocalContext.current

            var hasPermission by remember {
                mutableStateOf(
                    ContextCompat.checkSelfPermission(
                        context, Manifest.permission.CAMERA
                    ) == PackageManager.PERMISSION_GRANTED
                )
            }

            val view = LocalView.current
            SideEffect {
                val window = (view.context as? ComponentActivity)?.window ?: return@SideEffect
                val controller = WindowCompat.getInsetsController(window, view)
                controller.hide(WindowInsetsCompat.Type.systemBars())
                controller.systemBarsBehavior =
                    WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            }

            val launcher = rememberLauncherForActivityResult(
                ActivityResultContracts.RequestPermission()
            ) { granted -> hasPermission = granted }

            LaunchedEffect(Unit) {
                if (!hasPermission) launcher.launch(Manifest.permission.CAMERA)
            }

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

//reset session-----------------------------------------------------------------------------------
fun resetSession(isStreaming: Boolean) {
    if (!isStreaming) return

    glSurfaceView.queueEvent {
        try {
            val textureId = renderer?.cameraTextureId?.get(0) ?: return@queueEvent
            arSessionState.value?.close()
            arSessionState.value = null
            poseReady = false

            resetFramesRemaining = 10

            val newSession = Session(this@MainActivity).apply {
                val config = Config(this)
                config.updateMode = Config.UpdateMode.LATEST_CAMERA_IMAGE
                configure(config)
                setCameraTextureName(textureId)
                resume()
            }
            arSessionState.value = newSession
        } catch (e: Exception) {
            e.printStackTrace()
        }
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
//gl idk-----------------------------------------------------------------------------------
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
                val pose = camera.pose
                activity.latestTx = pose.tx().toDouble()
                activity.latestTy = pose.ty().toDouble()
                activity.latestTz = pose.tz().toDouble()
                activity.latestQw = pose.qw().toDouble()
                activity.latestQx = pose.qx().toDouble()
                activity.latestQy = pose.qy().toDouble()
                activity.latestQz = pose.qz().toDouble()
                activity.poseReady = true
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}

fun quatMul(
    qw: Double, qx: Double, qy: Double, qz: Double,
    pw: Double, px: Double, py: Double, pz: Double
): DoubleArray = doubleArrayOf(
    qw*pw - qx*px - qy*py - qz*pz,
    qw*px + qx*pw + qy*pz - qz*py,
    qw*py - qx*pz + qy*pw + qz*px,
    qw*pz + qx*py - qy*px + qz*pw
)

//enums-----------------------------------------------------------------------------------
enum class TouchUIMode(val label: String) {
    NONE("None"),
    HEADSET("Browser"),
    INDEX_RIGHT("Index Right"),//,
    INDEX_LEFT("Index Left"),
    //INDEX_SKELETAL("Index Skeletal")
    //INDEX_CONTROLLER("Index Controller")
}

enum class HardwareAction(val label: String) {
    NONE("none"),
    TRIGGER("trigger"),
    GRIP_HOLD("grip(hold)"),
    GRIP_TOGGLE("grip(toggle)")
}
//enums-----------------------------------------------------------------------------------

//ui-----------------------------------------------------------------------------------
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AROverlayUI(activity: MainActivity) {
    var currentPresetTrigger by remember { mutableStateOf("pass") }

    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("ar_settings", Context.MODE_PRIVATE) }
    val configuration = LocalConfiguration.current
    val isLandscape = configuration.screenWidthDp > configuration.screenHeightDp

    //persistent
    //todo: add offsets in ui
    var pitchOffset by remember {
        mutableStateOf(prefs.getFloat("PitchOffset", -90.0f).toDouble())
    }
    LaunchedEffect(pitchOffset) {
        activity.PitchOffset = pitchOffset
        prefs.edit().putFloat("PitchOffset", pitchOffset.toFloat()).apply()
    }

    var volUpState by remember {
        mutableStateOf(HardwareAction.valueOf(prefs.getString("volUp", HardwareAction.NONE.name) ?: HardwareAction.NONE.name))
    }
    var volDownState by remember {
        mutableStateOf(HardwareAction.valueOf(prefs.getString("volDown", HardwareAction.NONE.name) ?: HardwareAction.NONE.name))
    }
    var volUpDropdownExpanded by remember { mutableStateOf(false) }
    var volDownDropdownExpanded by remember { mutableStateOf(false) }
    LaunchedEffect(volUpState) {
        prefs.edit().putString("volUp", volUpState.name).apply()
        activity.volUpAction = volUpState // Keep the activity updated
    }
    LaunchedEffect(volDownState) {
        prefs.edit().putString("volDown", volDownState.name).apply()
        activity.volDownAction = volDownState // Keep the activity updated
    }

    var ipAddress by remember { mutableStateOf(prefs.getString("ip", null) ?: "192.168.50.83") }
    LaunchedEffect(ipAddress) { prefs.edit().putString("ip", ipAddress).apply() }

    var port by remember { mutableStateOf(prefs.getString("port", null) ?: "9001") }
    LaunchedEffect(port) { prefs.edit().putString("port", port).apply() }

    var isVertical by remember { mutableStateOf(prefs.getBoolean("vertical", false)) }
    LaunchedEffect(isVertical) {
        activity.isVertical = isVertical; prefs.edit().putBoolean("vertical", isVertical).apply()
    }

    var isStreaming by remember { mutableStateOf(prefs.getBoolean("streaming", false)) }
    LaunchedEffect(isStreaming) { prefs.edit().putBoolean("streaming", isStreaming).apply() }

    var touchUIMode by remember {
        mutableStateOf(
            TouchUIMode.valueOf(
                prefs.getString("touch_ui", TouchUIMode.NONE.name) ?: TouchUIMode.NONE.name
            )
        )
    }
    LaunchedEffect(touchUIMode) { prefs.edit().putString("touch_ui", touchUIMode.name).apply() }

    var browserUrl by remember {
        mutableStateOf(
            prefs.getString("browser_url", null) ?: "192.168.50.83:9999"
        )
    }
    LaunchedEffect(browserUrl) { prefs.edit().putString("browser_url", browserUrl).apply() }

    var settingsExpanded by remember { mutableStateOf(false) }
    var touchUIDropdownExpanded by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            var listenSocket: DatagramSocket? = null
            try {
                listenSocket = DatagramSocket(9002).apply { broadcast = true }
                val buffer = ByteArray(256)
                val packet = DatagramPacket(buffer, buffer.size)
                while (true) {
                    listenSocket.receive(packet)
                    val msg = String(packet.data, 0, packet.length, Charsets.UTF_8).trim()
                    if (msg == "RESET") {
                        activity.resetSession(isStreaming = isStreaming)
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                listenSocket?.close()
            }
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
                            configure(config)
                            setCameraTextureName(textureId)
                            resume()
                        }
                        activity.arSessionState.value = session
                    } else {
                        activity.arSessionState.value?.resume()
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        } else {
            activity.glSurfaceView.queueEvent {
                try {
                    activity.arSessionState.value?.pause()
                    activity.arSessionState.value?.close()
                    activity.arSessionState.value = null
                    activity.poseReady = false
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
    }

    LaunchedEffect(isStreaming) {
        if (!isStreaming) return@LaunchedEffect
        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            val socket = DatagramSocket()
            val address = InetAddress.getByName(ipAddress)
            val portInt = port.toIntOrNull() ?: 9001
            val posBuffer = ByteBuffer.allocate(25).order(ByteOrder.LITTLE_ENDIAN)
            val rotBuffer = ByteBuffer.allocate(33).order(ByteOrder.LITTLE_ENDIAN)
            val extraBuffer = ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN)
            val s = sin(Math.PI / 4)
            val c = cos(Math.PI / 4)

            //input: 'c' (1) + 12'?' (12) + 8'd' (64) = 77 bytes
            val inputBuffer = ByteBuffer.allocate(77).order(ByteOrder.LITTLE_ENDIAN)
            //skeletal: 'c' (1) + 25'd' (200) = 201 bytes
            val skeletalBuffer = ByteBuffer.allocate(201).order(ByteOrder.LITTLE_ENDIAN)

            //send data-----------------------------------------------------------------------------------
            while (isStreaming) {
                val tx = activity.latestTx;
                val ty = activity.latestTy;
                val tz = activity.latestTz
                var qw = activity.latestQw;
                var qx = activity.latestQx
                var qy = activity.latestQy;
                var qz = activity.latestQz

                if (activity.isVertical) {
                    val r = quatMul(qw, qx, qy, qz, c, 0.0, 0.0, -s)
                    val pOff = Math.toRadians(pitchOffset);
                    val rOff = Math.toRadians(180.0)
                    val cp = cos(pOff * 0.5);
                    val sp = sin(pOff * 0.5)
                    val cr = cos(rOff * 0.5);
                    val sr = sin(rOff * 0.5)
                    val finalR =
                        quatMul(r[0], r[1], r[2], r[3], cp * cr, sp * cr, -sp * sr, cp * sr)
                    qw = finalR[0]; qx = finalR[1]; qy = finalR[2]; qz = finalR[3]
                }

                //extra
                extraBuffer.clear()
                extraBuffer.put('E'.code.toByte())
                val isResetting = activity.resetFramesRemaining > 0
                extraBuffer.put(if (isResetting) 1.toByte() else 0.toByte())
                socket.send(
                    DatagramPacket(
                        extraBuffer.array(),
                        extraBuffer.capacity(),
                        address,
                        portInt
                    )
                )
                if (activity.resetFramesRemaining > 0) {
                    activity.resetFramesRemaining--
                }

                //position
                posBuffer.clear()
                posBuffer.put('P'.code.toByte())
                posBuffer.putDouble(tx); posBuffer.putDouble(ty); posBuffer.putDouble(tz)
                socket.send(
                    DatagramPacket(
                        posBuffer.array(),
                        posBuffer.capacity(),
                        address,
                        portInt
                    )
                )

                //rotation
                rotBuffer.clear()
                rotBuffer.put('R'.code.toByte())
                rotBuffer.putDouble(qw); rotBuffer.putDouble(qx)
                rotBuffer.putDouble(qy); rotBuffer.putDouble(qz)
                socket.send(
                    DatagramPacket(
                        rotBuffer.array(),
                        rotBuffer.capacity(),
                        address,
                        portInt
                    )
                )

                //input
                inputBuffer.clear()
                inputBuffer.put('I'.code.toByte())

                //unused failsafe
                activity.a_cap = activity.a
                activity.b_cap = activity.b
                activity.system_cap = activity.system

                if (activity.trigger > 0.1){
                    activity.trigger_cap = true
                    activity.trigger_btn = true
                }else{
                    activity.trigger_cap = false
                    activity.trigger_btn = false
                }

                if (activity.touch_x != 0.0 || activity.touch_y != 0.0 || activity.touch_force > 0.1){
                    activity.touch_cap = true
                }else{
                    activity.touch_cap = false
                }

                if (activity.joy_x != 0.0 || activity.joy_y != 0.0){
                    activity.joy_cap = true
                }else{
                    activity.joy_cap = false
                }

                if (activity.grip_force > 0.1){
                    activity.grip_pull = 1.0
                    activity.grip_cap = true
                }else{
                    activity.grip_pull = 0.0
                    activity.grip_cap = false
                }
                //unused failsafe

                val buttons = booleanArrayOf(
                    activity.a, activity.b, activity.system, activity.joy_btn, activity.trigger_btn,
                    activity.a_cap, activity.b_cap, activity.system_cap, activity.joy_cap,
                    activity.trigger_cap, activity.touch_cap, activity.grip_cap
                )
                for (btn in buttons) inputBuffer.put(if (btn) 1.toByte() else 0.toByte())

                inputBuffer.putDouble(activity.joy_x); inputBuffer.putDouble(activity.joy_y)
                inputBuffer.putDouble(activity.touch_x); inputBuffer.putDouble(activity.touch_y)
                inputBuffer.putDouble(activity.trigger); inputBuffer.putDouble(activity.touch_force)
                inputBuffer.putDouble(activity.grip_pull); inputBuffer.putDouble(activity.grip_force)
                socket.send(
                    DatagramPacket(
                        inputBuffer.array(),
                        inputBuffer.position(),
                        address,
                        portInt
                    )
                )

                //skeletal
                skeletalBuffer.clear()
                skeletalBuffer.put('S'.code.toByte())
                val isHandActive = activity.joy_x != 0.0 || activity.joy_y != 0.0 ||
                        activity.joy_btn || activity.touch_x != 0.0 ||
                        activity.touch_y != 0.0 || activity.touch_force != 0.0
                activity.flexions[0] = if (isHandActive) 1.0 else 0.0

                if (activity.trigger > 0.1) {
                    activity.flexions[4] = 1.0
                } else {
                    activity.flexions[4] = 0.0
                }

                if (activity.grip_cap) {
                    activity.flexions[8] = 1.0
                    activity.flexions[12] = 1.0
                    activity.flexions[16] = 1.0
                } else {
                    activity.flexions[8] = 0.0
                    activity.flexions[12] = 0.0
                    activity.flexions[16] = 0.0
                }

                for (f in activity.flexions) skeletalBuffer.putDouble(f)
                for (s in activity.splays) skeletalBuffer.putDouble(s)
                socket.send(
                    DatagramPacket(
                        skeletalBuffer.array(),
                        skeletalBuffer.position(),
                        address,
                        portInt
                    )
                )

                Thread.sleep(1)
            }
            socket.close()
        }
    }

    //bowser-----------------------------------------------------------------------------------
    Box(modifier = Modifier.fillMaxSize()) {
        if (touchUIMode == TouchUIMode.HEADSET) {
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { ctx ->
                    WebView(ctx).apply {
                        layoutParams = ViewGroup.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT
                        )
                        webViewClient = object : WebViewClient() {
                            override fun onReceivedSslError(
                                view: WebView,
                                handler: android.webkit.SslErrorHandler,
                                error: android.net.http.SslError
                            ) {
                                handler.proceed()
                            }
                        }
                        settings.javaScriptEnabled = true
                        settings.domStorageEnabled = true
                        loadUrl(browserUrl)
                    }
                }
            )
        }

        //index right-----------------------------------------------------------------------------------
        if (touchUIMode == TouchUIMode.INDEX_RIGHT) {
            Box(modifier = Modifier.fillMaxSize()) {
                Column(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = 230.dp, end = 0.dp),
                    horizontalAlignment = Alignment.End,
                    verticalArrangement = Arrangement.spacedBy(0.dp)
                ) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.padding(end = 8.dp)
                    ) {
                        var isSystemPressing by remember { mutableStateOf(false) }
                        Box(
                            modifier = Modifier
                                .width(300.dp)
                                .height(100.dp)
                                .background(Color(0xFF37474F), shape = RoundedCornerShape(14.dp))
                                .pointerInput(Unit) {
                                    detectTapGestures(onTap = {
                                        activity.resetSession(isStreaming = isStreaming)
                                    })
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "↺ reset",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                        Box(
                            modifier = Modifier
                                .width(100.dp)
                                .height(100.dp)
                                .background(
                                    if (isSystemPressing) Color(0xFF6A1B9A) else Color(0xFF3A0060),
                                    shape = RoundedCornerShape(14.dp)
                                )
                                .pointerInput(Unit) {
                                    detectTapGestures(onPress = {
                                        isSystemPressing = true
                                        activity.system = true
                                        tryAwaitRelease()
                                        isSystemPressing = false
                                        activity.system = false
                                    })
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "SYS",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                    }
                }
                Column(
                    modifier = Modifier.align(Alignment.CenterEnd),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    var joystickOffset by remember { mutableStateOf(Offset.Zero) }
                    val maxRadius = 80.dp
                    val maxRadiusPx = with(LocalDensity.current) { maxRadius.toPx() }

                    Box(
                        modifier = Modifier
                            .size(160.dp)
                            .background(Color.DarkGray.copy(alpha = 0.6f), shape = CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Box(
                            modifier = Modifier
                                .size(200.dp)
                                .pointerInput(Unit) {
                                    detectDragGestures(
                                        onDragEnd = {
                                            joystickOffset = Offset.Zero
                                            activity.joy_x = 0.0
                                            activity.joy_y = 0.0
                                        },
                                        onDragCancel = {
                                            joystickOffset = Offset.Zero
                                            activity.joy_x = 0.0
                                            activity.joy_y = 0.0
                                        },
                                        onDrag = { change, dragAmount ->
                                            change.consume()
                                            val newOffset = joystickOffset + dragAmount
                                            val distance = newOffset.getDistance()
                                            joystickOffset = if (distance <= maxRadiusPx) newOffset
                                            else newOffset / distance * maxRadiusPx
                                            activity.joy_x =
                                                (joystickOffset.x / maxRadiusPx).toDouble()
                                            activity.joy_y =
                                                -(joystickOffset.y / maxRadiusPx).toDouble()
                                        }
                                    )
                                }
                        )
                        Box(
                            modifier = Modifier
                                .offset {
                                    IntOffset(
                                        joystickOffset.x.roundToInt(),
                                        joystickOffset.y.roundToInt()
                                    )
                                }
                                .size(80.dp)
                                .background(Color(0xFF78909C), shape = CircleShape)
                        )
                    }

                    Box(
                        modifier = Modifier
                            .size(110.dp)
                            .background(Color(0xFF37474F), shape = RoundedCornerShape(20.dp))
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    activity.joy_btn = true; tryAwaitRelease(); activity.joy_btn =
                                    false
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "JOY",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 24.sp
                        )
                    }
                }
                Column(
                    modifier = Modifier.align(Alignment.Center),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    var isTouching by remember { mutableStateOf(false) }
                    Box(
                        modifier = Modifier
                            .width(120.dp)
                            .height(220.dp)
                            .background(
                                if (isTouching) Color(0xFF455A64) else Color(0xFF263238),
                                shape = RoundedCornerShape(16.dp)
                            )
                            .pointerInput(Unit) {
                                awaitPointerEventScope {
                                    while (true) {
                                        val event = awaitPointerEvent()
                                        val pointer = event.changes.firstOrNull()
                                        if (pointer != null && pointer.pressed) {
                                            isTouching = true
                                            activity.touch_cap = true
                                            val s = this.size
                                            activity.touch_x =
                                                ((pointer.position.x / s.width) * 2f - 1f).toDouble()
                                                    .coerceIn(-1.0, 1.0)
                                            activity.touch_y =
                                                -((pointer.position.y / s.height) * 2f - 1f).toDouble()
                                                    .coerceIn(-1.0, 1.0)
                                            pointer.consume()
                                        } else {
                                            isTouching = false
                                            activity.touch_cap = false
                                            activity.touch_x = 0.0
                                            activity.touch_y = 0.0
                                        }
                                    }
                                }
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text("TOUCHPAD", color = Color.Gray, fontSize = 11.sp)
                    }

                    var isForcePressing by remember { mutableStateOf(false) }
                    Box(
                        modifier = Modifier
                            .width(120.dp)
                            .height(56.dp)
                            .background(
                                if (isForcePressing) Color(0xFF00897B) else Color(0xFF004D40),
                                shape = RoundedCornerShape(14.dp)
                            )
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    isForcePressing = true
                                    activity.touch_force = 1.0
                                    tryAwaitRelease()
                                    isForcePressing = false
                                    activity.touch_force = 0.0
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "FORCE",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp
                        )
                    }
                }

                Column(
                    modifier = Modifier
                        .align(Alignment.CenterStart)
                        .padding(start = 0.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Box(
                        modifier = Modifier
                            .size(130.dp)
                            .background(Color(0xFFB71C1C), shape = RoundedCornerShape(20.dp))
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    activity.b = true; tryAwaitRelease(); activity.b = false
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "B",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 36.sp
                        )
                    }

                    Box(
                        modifier = Modifier
                            .size(130.dp)
                            .background(Color(0xFF1565C0), shape = RoundedCornerShape(20.dp))
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    activity.a = true; tryAwaitRelease(); activity.a = false
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "A",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 36.sp
                        )
                    }
                }

                Column(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {

                    var isTriggerPressing by remember { mutableStateOf(false) }
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 32.dp)
                            .height(150.dp)
                            .background(
                                if (isTriggerPressing) Color(0xFFFF6F00) else Color(0xFF7B3F00),
                                shape = RoundedCornerShape(16.dp)
                            )
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    isTriggerPressing = true
                                    activity.trigger = 1.0
                                    tryAwaitRelease()
                                    isTriggerPressing = false
                                    activity.trigger = 0.0
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "TRIGGER",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 20.sp
                        )
                    }

                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 32.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {

                        var isGripToggled by remember { mutableStateOf(false) }
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .height(150.dp)
                                .background(
                                    if (isGripToggled) Color(0xFF558B2F) else Color(0xFF2E4A1A),
                                    shape = RoundedCornerShape(16.dp)
                                )
                                .pointerInput(Unit) {
                                    detectTapGestures(
                                        onTap = {
                                            isGripToggled = !isGripToggled
                                            activity.grip_force = if (isGripToggled) 1.0 else 0.0
                                        }
                                    )
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                if (isGripToggled) "GRIP\nON" else "GRIP\nOFF",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }

                        var isGripHolding by remember { mutableStateOf(false) }
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .height(150.dp)
                                .background(
                                    if (isGripHolding) Color(0xFF558B2F) else Color(0xFF2E4A1A),
                                    shape = RoundedCornerShape(16.dp)
                                )
                                .pointerInput(isGripToggled) {
                                    detectTapGestures(onPress = {
                                        isGripHolding = true
                                        activity.grip_force = if (isGripToggled) 0.0 else 1.0
                                        tryAwaitRelease()
                                        isGripHolding = false
                                        activity.grip_force = if (isGripToggled) 1.0 else 0.0
                                    })
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "GRIP\n(hold)",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                    }
                }
            }
        }
        //index left-----------------------------------------------------------------------------------
        if (touchUIMode == TouchUIMode.INDEX_LEFT) {
            Box(modifier = Modifier.fillMaxSize()) {

                Column(
                    modifier = Modifier
                        .align(Alignment.TopStart)
                        .padding(top = 230.dp, start = 0.dp),
                    horizontalAlignment = Alignment.Start,
                    verticalArrangement = Arrangement.spacedBy(0.dp)
                ) {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.padding(start = 8.dp)
                    ) {
                        var isSystemPressing by remember { mutableStateOf(false) }
                        Box(
                            modifier = Modifier
                                .width(100.dp)
                                .height(100.dp)
                                .background(
                                    if (isSystemPressing) Color(0xFF6A1B9A) else Color(0xFF3A0060),
                                    shape = RoundedCornerShape(14.dp)
                                )
                                .pointerInput(Unit) {
                                    detectTapGestures(onPress = {
                                        isSystemPressing = true
                                        activity.system = true
                                        tryAwaitRelease()
                                        isSystemPressing = false
                                        activity.system = false
                                    })
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "SYS",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                        Box(
                            modifier = Modifier
                                .width(300.dp)
                                .height(100.dp)
                                .background(Color(0xFF37474F), shape = RoundedCornerShape(14.dp))
                                .pointerInput(Unit) {
                                    detectTapGestures(onTap = {
                                        activity.resetSession(isStreaming = isStreaming)
                                    })
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "↺ RESET",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                    }
                }

                Column(
                    modifier = Modifier.align(Alignment.CenterStart),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                ) {
                    var joystickOffset by remember { mutableStateOf(Offset.Zero) }
                    val maxRadius = 80.dp
                    val maxRadiusPx = with(LocalDensity.current) { maxRadius.toPx() }

                    Box(
                        modifier = Modifier
                            .size(160.dp)
                            .background(Color.DarkGray.copy(alpha = 0.6f), shape = CircleShape),
                        contentAlignment = Alignment.Center
                    ) {
                        Box(
                            modifier = Modifier
                                .size(200.dp)
                                .pointerInput(Unit) {
                                    detectDragGestures(
                                        onDragEnd = {
                                            joystickOffset = Offset.Zero
                                            activity.joy_x = 0.0
                                            activity.joy_y = 0.0
                                        },
                                        onDragCancel = {
                                            joystickOffset = Offset.Zero
                                            activity.joy_x = 0.0
                                            activity.joy_y = 0.0
                                        },
                                        onDrag = { change, dragAmount ->
                                            change.consume()
                                            val newOffset = joystickOffset + dragAmount
                                            val distance = newOffset.getDistance()
                                            joystickOffset = if (distance <= maxRadiusPx) newOffset
                                            else newOffset / distance * maxRadiusPx
                                            activity.joy_x =
                                                (joystickOffset.x / maxRadiusPx).toDouble()
                                            activity.joy_y =
                                                -(joystickOffset.y / maxRadiusPx).toDouble()
                                        }
                                    )
                                }
                        )
                        Box(
                            modifier = Modifier
                                .offset {
                                    IntOffset(
                                        joystickOffset.x.roundToInt(),
                                        joystickOffset.y.roundToInt()
                                    )
                                }
                                .size(80.dp)
                                .background(Color(0xFF78909C), shape = CircleShape)
                        )
                    }

                    Box(
                        modifier = Modifier
                            .size(110.dp)
                            .background(Color(0xFF37474F), shape = RoundedCornerShape(20.dp))
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    activity.joy_btn = true; tryAwaitRelease(); activity.joy_btn =
                                    false
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "JOY",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 24.sp
                        )
                    }
                }

                Column(
                    modifier = Modifier.align(Alignment.Center),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    var isTouching by remember { mutableStateOf(false) }
                    Box(
                        modifier = Modifier
                            .width(120.dp)
                            .height(220.dp)
                            .background(
                                if (isTouching) Color(0xFF455A64) else Color(0xFF263238),
                                shape = RoundedCornerShape(16.dp)
                            )
                            .pointerInput(Unit) {
                                awaitPointerEventScope {
                                    while (true) {
                                        val event = awaitPointerEvent()
                                        val pointer = event.changes.firstOrNull()
                                        if (pointer != null && pointer.pressed) {
                                            isTouching = true
                                            activity.touch_cap = true
                                            val s = this.size
                                            activity.touch_x =
                                                ((pointer.position.x / s.width) * 2f - 1f).toDouble()
                                                    .coerceIn(-1.0, 1.0)
                                            activity.touch_y =
                                                -((pointer.position.y / s.height) * 2f - 1f).toDouble()
                                                    .coerceIn(-1.0, 1.0)
                                            pointer.consume()
                                        } else {
                                            isTouching = false
                                            activity.touch_cap = false
                                            activity.touch_x = 0.0
                                            activity.touch_y = 0.0
                                        }
                                    }
                                }
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text("TOUCHPAD", color = Color.Gray, fontSize = 11.sp)
                    }

                    var isForcePressing by remember { mutableStateOf(false) }
                    Box(
                        modifier = Modifier
                            .width(120.dp)
                            .height(56.dp)
                            .background(
                                if (isForcePressing) Color(0xFF00897B) else Color(0xFF004D40),
                                shape = RoundedCornerShape(14.dp)
                            )
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    isForcePressing = true
                                    activity.touch_force = 1.0
                                    tryAwaitRelease()
                                    isForcePressing = false
                                    activity.touch_force = 0.0
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "FORCE",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp
                        )
                    }
                }

                Column(
                    modifier = Modifier
                        .align(Alignment.CenterEnd)
                        .padding(end = 0.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Box(
                        modifier = Modifier
                            .size(130.dp)
                            .background(Color(0xFFB71C1C), shape = RoundedCornerShape(20.dp))
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    activity.b = true; tryAwaitRelease(); activity.b = false
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "B",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 36.sp
                        )
                    }

                    Box(
                        modifier = Modifier
                            .size(130.dp)
                            .background(Color(0xFF1565C0), shape = RoundedCornerShape(20.dp))
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    activity.a = true; tryAwaitRelease(); activity.a = false
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "A",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 36.sp
                        )
                    }
                }

                Column(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    var isTriggerPressing by remember { mutableStateOf(false) }
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 32.dp)
                            .height(150.dp)
                            .background(
                                if (isTriggerPressing) Color(0xFFFF6F00) else Color(0xFF7B3F00),
                                shape = RoundedCornerShape(16.dp)
                            )
                            .pointerInput(Unit) {
                                detectTapGestures(onPress = {
                                    isTriggerPressing = true
                                    activity.trigger = 1.0
                                    tryAwaitRelease()
                                    isTriggerPressing = false
                                    activity.trigger = 0.0
                                })
                            },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            "TRIGGER",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 20.sp
                        )
                    }

                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 32.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {

                        var isGripHolding by remember { mutableStateOf(false) }
                        var isGripToggled by remember { mutableStateOf(false) }
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .height(150.dp)
                                .background(
                                    if (isGripHolding) Color(0xFF558B2F) else Color(0xFF2E4A1A),
                                    shape = RoundedCornerShape(16.dp)
                                )
                                .pointerInput(isGripToggled) {
                                    detectTapGestures(onPress = {
                                        isGripHolding = true
                                        activity.grip_force = if (isGripToggled) 0.0 else 1.0
                                        tryAwaitRelease()
                                        isGripHolding = false
                                        activity.grip_force = if (isGripToggled) 1.0 else 0.0
                                    })
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                "GRIP\n(hold)",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }

                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .height(150.dp)
                                .background(
                                    if (isGripToggled) Color(0xFF558B2F) else Color(0xFF2E4A1A),
                                    shape = RoundedCornerShape(16.dp)
                                )
                                .pointerInput(Unit) {
                                    detectTapGestures(
                                        onTap = {
                                            isGripToggled = !isGripToggled
                                            activity.grip_force = if (isGripToggled) 1.0 else 0.0
                                        }
                                    )
                                },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                if (isGripToggled) "GRIP\nON" else "GRIP\nOFF",
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                        }
                    }
                }
            }
        }
        //index controller-----------------------------------------------------------------------
        //if (touchUIMode == TouchUIMode.INDEX_CONTROLLER) {
        if (true != true){
            SuperButton(
                id = "btn_A",
                label = "A",
                isActive = activity.a,
                onToggle = { activity.a = it },
                defaultX = 50f,
                defaultY = 100f,
                prefs = prefs,
                activity = activity
            )

            SuperButton(
                id = "btn_B",
                label = "B",
                isActive = activity.b,
                onToggle = { activity.b = it },
                defaultX = 150f,
                defaultY = 100f,
                prefs = prefs,
                activity = activity
            )

            SuperButton(
                id = "btn_SYS",
                label = "SYS",
                isActive = activity.system,
                onToggle = { activity.system = it },
                defaultX = 250f,
                defaultY = 100f,
                prefs = prefs,
                activity = activity
            )
        }

        //nav bar-----------------------------------------------------------------------------------
        val uriHandler = LocalUriHandler.current
        if (isLandscape) {
            Column(
                modifier = Modifier
                    .fillMaxHeight()
                    .width(32.dp)
                    .background(Color.Black.copy(alpha = 0.55f))
                    .padding(4.dp),
                verticalArrangement = Arrangement.Top,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                IconTextButton(
                    label = "⚙",
                    modifier = Modifier.fillMaxWidth().height(64.dp),
                    onClick = { settingsExpanded = !settingsExpanded }
                )
                Spacer(modifier = Modifier.height(4.dp))
                RotatedResetButton(
                    modifier = Modifier.weight(1f).fillMaxWidth(),
                    onClick = { activity.resetSession(isStreaming = isStreaming) }
                )
            }
        } else {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .wrapContentHeight()
                    .background(Color.Black.copy(alpha = 0.55f))
                    .padding(4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconTextButton(
                    label = "⚙",
                    modifier = Modifier.size(64.dp),
                    onClick = { settingsExpanded = !settingsExpanded }
                )
                Spacer(modifier = Modifier.width(4.dp))
                Button(
                    onClick = { activity.resetSession(isStreaming = isStreaming) },
                    modifier = Modifier.weight(1f).height(64.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color.Gray),
                    contentPadding = PaddingValues(0.dp),
                    shape = MaterialTheme.shapes.small
                ) {
                    Text("↺", fontSize = 14.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
        //settings card-----------------------------------------------------------------------------------
        if (settingsExpanded) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(top = 44.dp)
            ) {
                Card(
                    modifier = Modifier
                        .wrapContentSize()
                        .padding(8.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = Color(0xFF1A1A2E).copy(alpha = 0.95f)
                    ),
                    elevation = CardDefaults.cardElevation(8.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .padding(16.dp)
                            .verticalScroll(rememberScrollState())
                            .widthIn(min = 260.dp, max = 340.dp)
                    ) {
                        Text(
                            "Settings",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp,
                            modifier = Modifier.padding(bottom = 12.dp)
                        )

                        val displayMetrics = LocalContext.current.resources.displayMetrics
                        val widthPx = displayMetrics.widthPixels
                        val heightPx = displayMetrics.heightPixels
                        val density = displayMetrics.density
                        val widthDp = (widthPx / density).toInt()
                        val heightDp = (heightPx / density).toInt()

                        Text("Resolution", color = Color.Gray, fontSize = 11.sp)
                        Text(
                            "${widthPx} × ${heightPx} px  (${widthDp} × ${heightDp} dp)",
                            color = Color.White,
                            fontSize = 12.sp,
                            modifier = Modifier.padding(bottom = 10.dp)
                        )

                        Text("Host IP", color = Color.Gray, fontSize = 11.sp)
                        OutlinedTextField(
                            value = ipAddress,
                            onValueChange = { ipAddress = it },
                            singleLine = true,
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = Color(0xFF5C6BC0),
                                unfocusedBorderColor = Color.Gray
                            ),
                            modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp)
                        )

                        Text("Port", color = Color.Gray, fontSize = 11.sp)
                        OutlinedTextField(
                            value = port,
                            onValueChange = { newValue ->
                                if (newValue.isEmpty() || newValue.all { it.isDigit() }) {
                                    port = newValue
                                }
                            },
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = Color(0xFF5C6BC0),
                                unfocusedBorderColor = Color.Gray
                            ),
                            modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp)
                        )

                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
                        ) {
                            Checkbox(
                                checked = isVertical,
                                onCheckedChange = { isVertical = it },
                                colors = CheckboxDefaults.colors(checkedColor = Color(0xFF5C6BC0))
                            )
                            Text(
                                if (isVertical) "Vertical (portrait)" else "Horizontal (landscape)",
                                color = Color.White,
                                fontSize = 13.sp
                            )
                        }

                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
                        ) {
                            Checkbox(
                                checked = isStreaming,
                                onCheckedChange = { isStreaming = it },
                                colors = CheckboxDefaults.colors(
                                    checkedColor = Color(0xFF43A047),
                                    uncheckedColor = Color.Gray
                                )
                            )
                            Text(
                                if (isStreaming) "Streaming ON" else "Streaming OFF",
                                color = if (isStreaming) Color(0xFF81C784) else Color.White,
                                fontSize = 13.sp
                            )
                        }

                        Text("Vertical Pitch Offset(default -90.0)", color = Color.Gray, fontSize = 11.sp)
                        OutlinedTextField(
                            value = pitchOffset.toString(),
                            onValueChange = { newValue: String ->
                                if (newValue.isEmpty() || newValue == "-" || newValue.matches(Regex("-?\\d*\\.?\\d*"))) {
                                    pitchOffset = newValue.toDoubleOrNull() ?: pitchOffset
                                }
                            },
                            singleLine = true,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = Color(0xFF5C6BC0),
                                unfocusedBorderColor = Color.Gray
                            ),
                            modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp)
                        )

                        Text("Browser URL", color = Color.Gray, fontSize = 11.sp)
                        OutlinedTextField(
                            value = browserUrl,
                            onValueChange = { browserUrl = it },
                            singleLine = true,
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedTextColor = Color.White,
                                unfocusedTextColor = Color.White,
                                focusedBorderColor = Color(0xFF5C6BC0),
                                unfocusedBorderColor = Color.Gray
                            ),
                            modifier = Modifier.fillMaxWidth()
                                .padding(top = 4.dp, bottom = 10.dp)
                        )

//                        HorizontalDivider(
//                            color = Color.Gray.copy(alpha = 0.3f),
//                            modifier = Modifier.padding(vertical = 4.dp)
//                        )

                        Text(
                            "Touch UI",
                            color = Color.Gray,
                            fontSize = 11.sp,
                            modifier = Modifier.padding(bottom = 4.dp)
                        )
                        ExposedDropdownMenuBox(
                            expanded = touchUIDropdownExpanded,
                            onExpandedChange = { touchUIDropdownExpanded = it }
                        ) {
                            OutlinedTextField(
                                value = touchUIMode.label,
                                onValueChange = {},
                                readOnly = true,
                                trailingIcon = {
                                    ExposedDropdownMenuDefaults.TrailingIcon(
                                        expanded = touchUIDropdownExpanded
                                    )
                                },
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White,
                                    unfocusedTextColor = Color.White,
                                    focusedBorderColor = Color(0xFF5C6BC0),
                                    unfocusedBorderColor = Color.Gray
                                ),
                                modifier = Modifier.menuAnchor().fillMaxWidth()
                            )
                            ExposedDropdownMenu(
                                expanded = touchUIDropdownExpanded,
                                onDismissRequest = { touchUIDropdownExpanded = false },
                                containerColor = Color(0xFF1A1A2E)
                            ) {
                                TouchUIMode.entries.forEach { mode ->
                                    DropdownMenuItem(
                                        text = { Text(mode.label, color = Color.White) },
                                        onClick = {
                                            touchUIMode = mode
                                            touchUIDropdownExpanded = false
                                        }
                                    )
                                }
                            }
                        }

                        //readd later---------------------------------------------------------------
//                        Row(
//                            verticalAlignment = Alignment.CenterVertically,
//                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
//                        ) {
//                            Checkbox(
//                                checked = activity.InEdit,
//                                onCheckedChange = { activity.InEdit = it }, // Directly flips the main variable
//                                colors = CheckboxDefaults.colors(
//                                    checkedColor = Color(0xFF43A047),
//                                    uncheckedColor = Color.Gray
//                                )
//                            )
//                            Text(
//                                text = if (activity.InEdit) "Editing" else "Not Editing",
//                                color = if (activity.InEdit) Color(0xFF81C784) else Color.White,
//                                fontSize = 13.sp
//                            )
//                        }

//                        PresetLayoutComboBox(prefs = prefs, activity = activity)

                        //readd later---------------------------------------------------------------

                        Text("Volume Up Action", color = Color.Gray, fontSize = 11.sp, modifier = Modifier.padding(bottom = 4.dp))
                        ExposedDropdownMenuBox(
                            expanded = volUpDropdownExpanded,
                            onExpandedChange = { volUpDropdownExpanded = it }
                        ) {
                            OutlinedTextField(
                                value = volUpState.label,
                                onValueChange = {},
                                readOnly = true,
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = volUpDropdownExpanded) },
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White, unfocusedTextColor = Color.White,
                                    focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray
                                ),
                                modifier = Modifier.menuAnchor().fillMaxWidth()
                            )
                            ExposedDropdownMenu(
                                expanded = volUpDropdownExpanded,
                                onDismissRequest = { volUpDropdownExpanded = false },
                                containerColor = Color(0xFF1A1A2E)
                            ) {
                                HardwareAction.entries.forEach { action ->
                                    DropdownMenuItem(
                                        text = { Text(action.label, color = Color.White) },
                                        onClick = {
                                            volUpState = action
                                            activity.volUpAction = action
                                            activity.sharedPrefs.edit().putString("volUp", action.name).apply()
                                            volUpDropdownExpanded = false
                                        }
                                    )
                                }
                            }
                        }
                        Text("Volume Down Action", color = Color.Gray, fontSize = 11.sp, modifier = Modifier.padding(bottom = 4.dp))
                        ExposedDropdownMenuBox(
                            expanded = volDownDropdownExpanded,
                            onExpandedChange = { volDownDropdownExpanded = it }
                        ) {
                            OutlinedTextField(
                                value = volDownState.label,
                                onValueChange = {},
                                readOnly = true,
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = volDownDropdownExpanded) },
                                colors = OutlinedTextFieldDefaults.colors(
                                    focusedTextColor = Color.White, unfocusedTextColor = Color.White,
                                    focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray
                                ),
                                modifier = Modifier.menuAnchor().fillMaxWidth()
                            )
                            ExposedDropdownMenu(
                                expanded = volDownDropdownExpanded,
                                onDismissRequest = { volDownDropdownExpanded = false },
                                containerColor = Color(0xFF1A1A2E)
                            ) {
                                HardwareAction.entries.forEach { action ->
                                    DropdownMenuItem(
                                        text = { Text(action.label, color = Color.White) },
                                        onClick = {
                                            volDownState = action
                                            activity.volDownAction = action
                                            activity.sharedPrefs.edit().putString("volDown", action.name).apply()
                                            volDownDropdownExpanded = false
                                        }
                                    )
                                }
                            }
                        }

                        Text(
                            "Made By: DaniXmir",
                            color = Color.White,
                            fontSize = 24.sp,
                            modifier = Modifier.padding(bottom = 4.dp)
                        )

                        GifButton()

                        Row {
                            Text(
                                text = "youtube!",
                                color = Color(0xFF5C6BC0),
                                fontSize = 22.sp,
                                textDecoration = TextDecoration.Underline,
                                modifier = Modifier
                                    .clickable { uriHandler.openUri("https://www.youtube.com/") }
                                    .padding(vertical = 4.dp)
                            )
                            Text(
                                "   ",
                                color = Color.White,
                                fontSize = 24.sp,
                                modifier = Modifier.padding(bottom = 4.dp)
                            )
                            Text(
                                text = "github!",
                                color = Color(0xFF5C6BC0),
                                fontSize = 22.sp,
                                textDecoration = TextDecoration.Underline,
                                modifier = Modifier
                                    .clickable { uriHandler.openUri("https://github.com/DaniXmir/GlassVr") }
                                    .padding(vertical = 4.dp)
                            )
                            Text(
                                "   ",
                                color = Color.White,
                                fontSize = 24.sp,
                                modifier = Modifier.padding(bottom = 4.dp)
                            )
                            Text(
                                text = "discord!",
                                color = Color(0xFF5C6BC0),
                                fontSize = 22.sp,
                                textDecoration = TextDecoration.Underline,
                                modifier = Modifier
                                    .clickable { uriHandler.openUri("https://discord.com/invite/jyvWdKBpPj") }
                                    .padding(vertical = 4.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

//composable buttons--------------------------------------------------------------------------------
//nav bar
@Composable
fun IconTextButton(
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onClick,
        modifier = modifier,
        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF37474F)),
        contentPadding = PaddingValues(0.dp)
    ) {
        Text(label, fontSize = 16.sp)
    }
}

@Composable
fun RotatedResetButton(modifier: Modifier = Modifier, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        modifier = modifier,
        colors = ButtonDefaults.buttonColors(containerColor = Color.Gray),
        contentPadding = PaddingValues(0.dp),
        shape = MaterialTheme.shapes.small
    ) {
        Text(
            "↺",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = Color.White
        )
    }
}
//extra
@Composable
fun GifButton() {
    val context = LocalContext.current

    AsyncImage(
        model = ImageRequest.Builder(context)
            .data(R.drawable.fix_anim)
            .decoderFactory(GifDecoder.Factory())
            .build(),
        contentDescription = "Alert Button",
        modifier = Modifier
            .size(200.dp)
            .clickable {
                //2008 (Android 1.0)
                val alertContext = ContextThemeWrapper(context, android.R.style.Theme_Dialog)

                //2011 (Android 3.0/4.0)
                //val alertContext = ContextThemeWrapper(context, android.R.style.Theme_Holo_Dialog)

                //2012 (Android 4.0.3)
                //val alertContext = ContextThemeWrapper(context, android.R.style.Theme_DeviceDefault_Dialog)

                //2014 (Android 5.0)
                //val alertContext = ContextThemeWrapper(context, android.R.style.Theme_Material_Dialog)

                AlertDialog.Builder(alertContext)
                    .setTitle(";P")
                    .setMessage("OUCH!")
                    .setPositiveButton("ok") { dialog, _ ->
                        dialog.dismiss()
                    }
                    .create()
                    .show()
            }
        )
}

@Composable
fun Gif() {
    AsyncImage(
        model = ImageRequest.Builder(LocalContext.current)
            .data(R.drawable.fix_anim)
            .decoderFactory(GifDecoder.Factory())
            .build(),
        contentDescription = null,
        modifier = Modifier.size(200.dp)
    )
}

//index layouts
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PresetLayoutComboBox(
    prefs: android.content.SharedPreferences,
    activity: MainActivity
) {
    val options = listOf("pass", "one")
    var expanded by remember { mutableStateOf(false) }
    var selectedOption by remember { mutableStateOf(options[0]) }

    Box(modifier = Modifier.padding(vertical = 8.dp)) {
        ExposedDropdownMenuBox(
            expanded = expanded,
            onExpandedChange = { expanded = it }
        ) {
            OutlinedTextField(
                modifier = Modifier.menuAnchor().fillMaxWidth(),
                readOnly = true,
                value = selectedOption,
                onValueChange = {},
                label = { Text("Preset Layout", color = Color.White) },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White,
                    focusedBorderColor = Color(0xFF0288D1),
                    unfocusedBorderColor = Color.Gray
                )
            )

            ExposedDropdownMenu(
                expanded = expanded,
                onDismissRequest = { expanded = false }
            ) {
                options.forEach { option ->
                    DropdownMenuItem(
                        text = { Text(option) },
                        onClick = {
                            selectedOption = option
                            expanded = false

                            if (option == "one") {
                                prefs.edit().apply {
                                    // Including width/height so your resizable buttons don't break!
                                    putFloat("btn_A_x", 100f)
                                    putFloat("btn_A_y", 150f)
                                    putFloat("btn_A_width", 80f)
                                    putFloat("btn_A_height", 80f)

                                    putFloat("btn_B_x", 250f)
                                    putFloat("btn_B_y", 150f)
                                    putFloat("btn_B_width", 80f)
                                    putFloat("btn_B_height", 80f)

                                    putFloat("btn_SYS_x", 400f)
                                    putFloat("btn_SYS_y", 150f)
                                    putFloat("btn_SYS_width", 80f)
                                    putFloat("btn_SYS_height", 80f)
                                }.apply()

                                // THIS IS THE FIX: Just increment the trigger.
                                // Compose sees the number change and instantly redraws the buttons.
                                activity.layoutRefreshTrigger++
                            }
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun SuperButton(
    id: String,
    label: String,
    isActive: Boolean,
    onToggle: (Boolean) -> Unit,
    defaultX: Float,
    defaultY: Float,
    defaultWidth: Float = 80f,
    defaultHeight: Float = 80f,
    prefs: android.content.SharedPreferences,
    activity: MainActivity
) {
    val isEditMode = activity.InEdit
    val refreshTrigger = activity.layoutRefreshTrigger // Catch the trigger signal

    // Pass BOTH variables as keys. If either one changes, the cache clears and reloads from disk!
    var offsetX by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_x", defaultX)) }
    var offsetY by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_y", defaultY)) }
    var widthDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_width", defaultWidth)) }
    var heightDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_height", defaultHeight)) }

    // Interaction Tracking Flags
    var isDragging by remember { mutableStateOf(false) }
    var isResizing by remember { mutableStateOf(false) }

    Box(
        modifier = Modifier
            .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
            .requiredSize(width = widthDp.dp, height = heightDp.dp)
            .background(if (isActive) Color.Blue else Color.DarkGray, RoundedCornerShape(12.dp))
            .pointerInput(isEditMode) {
                if (isEditMode) {
                    detectDragGestures(
                        onDragStart = { isDragging = true },
                        onDragEnd = {
                            isDragging = false
                            prefs.edit()
                                .putFloat("${id}_x", offsetX)
                                .putFloat("${id}_y", offsetY)
                                .apply()
                        },
                        onDrag = { change, dragAmount ->
                            change.consume()
                            offsetX += dragAmount.x
                            offsetY += dragAmount.y
                        }
                    )
                } else {
                    detectTapGestures(onPress = {
                        onToggle(true)
                        tryAwaitRelease()
                        onToggle(false)
                    })
                }
            },
        contentAlignment = Alignment.Center
    ) {
        // Dynamic Text Telemetry Overlay
        if (isEditMode && (isDragging || isResizing)) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "X:${offsetX.roundToInt()} Y:${offsetY.roundToInt()}",
                    color = Color.Green,
                    fontSize = 10.sp,
                    lineHeight = 11.sp
                )
                Text(
                    text = "W:${widthDp.roundToInt()} H:${heightDp.roundToInt()}",
                    color = Color.Cyan,
                    fontSize = 10.sp
                )
            }
        } else {
            val minDimension = minOf(widthDp, heightDp)
            Text(label, color = Color.White, fontSize = (minDimension * 0.25f).sp)
        }

        // Custom Resize Handle
        if (isEditMode) {
            Box(
                modifier = Modifier
                    .size(24.dp)
                    .align(Alignment.BottomEnd)
                    .background(Color(0x88FFEB3B), RoundedCornerShape(topStart = 8.dp, bottomEnd = 12.dp))
                    .pointerInput(Unit) {
                        detectDragGestures(
                            onDragStart = { isResizing = true },
                            onDragEnd = {
                                isResizing = false
                                prefs.edit()
                                    .putFloat("${id}_width", widthDp)
                                    .putFloat("${id}_height", heightDp)
                                    .apply()
                            },
                            onDrag = { change, dragAmount ->
                                change.consume()
                                widthDp = (widthDp + dragAmount.x).coerceAtLeast(50f)
                                heightDp = (heightDp + dragAmount.y).coerceAtLeast(50f)
                            }
                        )
                    }
            ) {
                Text("⤡", color = Color.Black, fontSize = 10.sp, modifier = Modifier.align(Alignment.Center))
            }
        }
    }
}

//;P

























































//todo: anchor test
//package com.example.GlassVR
//
//import android.Manifest
//import android.content.Context
//import android.content.pm.PackageManager
//import android.opengl.GLES20
//import android.opengl.GLSurfaceView
//import android.os.Bundle
//import android.view.ViewGroup
//import android.webkit.WebView
//import android.webkit.WebViewClient
//import androidx.activity.ComponentActivity
//import androidx.activity.SystemBarStyle
//import androidx.activity.compose.rememberLauncherForActivityResult
//import androidx.activity.compose.setContent
//import androidx.activity.enableEdgeToEdge
//import androidx.activity.result.contract.ActivityResultContracts
//import androidx.core.content.ContextCompat
//import androidx.core.view.WindowCompat
//import androidx.core.view.WindowInsetsCompat
//import androidx.core.view.WindowInsetsControllerCompat
//
//import androidx.compose.foundation.background
//import androidx.compose.foundation.layout.*
//import androidx.compose.foundation.rememberScrollState
//import androidx.compose.foundation.verticalScroll
//import androidx.compose.foundation.shape.CircleShape
//import androidx.compose.material3.*
//import androidx.compose.runtime.*
//import androidx.compose.ui.Alignment
//import androidx.compose.ui.Modifier
//import androidx.compose.ui.graphics.Color
//import androidx.compose.ui.graphics.toArgb
//import androidx.compose.ui.platform.LocalConfiguration
//import androidx.compose.ui.platform.LocalContext
//import androidx.compose.ui.platform.LocalView
//import androidx.compose.ui.text.font.FontWeight
//import androidx.compose.ui.unit.dp
//import androidx.compose.ui.unit.sp
//import androidx.compose.ui.viewinterop.AndroidView
//
//import androidx.compose.foundation.gestures.detectDragGestures
//import androidx.compose.foundation.gestures.detectTapGestures
//import androidx.compose.ui.input.pointer.pointerInput
//
//import com.google.ar.core.Config
//import com.google.ar.core.Frame
//import com.google.ar.core.Session
//import com.google.ar.core.TrackingState
//import java.net.DatagramPacket
//import java.net.DatagramSocket
//import java.net.InetAddress
//import java.nio.ByteBuffer
//import java.nio.ByteOrder
//import javax.microedition.khronos.egl.EGLConfig
//import javax.microedition.khronos.opengles.GL10
//import kotlin.math.cos
//import kotlin.math.sin
//
//import kotlin.math.roundToInt
//import androidx.compose.foundation.shape.RoundedCornerShape
//import androidx.compose.ui.geometry.Offset
//import androidx.compose.ui.platform.LocalDensity
//import androidx.compose.ui.unit.IntOffset
//
//import coil.compose.AsyncImage
//import coil.request.ImageRequest
//import coil.decode.GifDecoder
//
//import androidx.compose.ui.platform.LocalUriHandler
//import androidx.compose.ui.text.style.TextDecoration
//import androidx.compose.foundation.clickable
//import android.view.KeyEvent
//
//import android.widget.Toast
//import androidx.compose.foundation.layout.size
//import androidx.compose.runtime.Composable
//
//import androidx.compose.foundation.gestures.detectDragGestures
//import kotlin.math.roundToInt
//
//import android.app.AlertDialog
//import android.view.ContextThemeWrapper
//
//import androidx.compose.foundation.text.KeyboardOptions
//import androidx.compose.ui.text.input.KeyboardType
//
//class MainActivity : ComponentActivity() {
//    var InEdit by mutableStateOf(false)
//    var layoutRefreshTrigger by mutableStateOf(0)
//
//    val arSessionState = mutableStateOf<Session?>(null)
//    lateinit var glSurfaceView: GLSurfaceView
//    var renderer: ArRenderer? = null
//
//    @Volatile var isVertical = false
//    @Volatile var sendResetPacket = false
//    @Volatile var resetFramesRemaining = 0
//    @Volatile var originAnchor: com.google.ar.core.Anchor? = null
//
//    //pos-rot
//    @Volatile var latestTx = 0.0
//    @Volatile var latestTy = 0.0
//    @Volatile var latestTz = 0.0
//    @Volatile var latestQw = 1.0
//    @Volatile var latestQx = 0.0
//    @Volatile var latestQy = 0.0
//    @Volatile var latestQz = 0.0
//    @Volatile var poseReady = false
//
//    //offsets
//    @Volatile var PitchOffset = -90.0
//
//    //input (valve index controllers have a crazy level of configurability)
//    @Volatile var a = false
//    @Volatile var a_cap = false
//    @Volatile var b = false
//    @Volatile var b_cap = false
//    @Volatile var system = false
//    @Volatile var system_cap = false
//    @Volatile var touch_cap = false
//    @Volatile var grip_cap = false
//    @Volatile var joy_x = 0.0
//    @Volatile var joy_y = 0.0
//    @Volatile var joy_btn = false
//    @Volatile var joy_cap = false
//    @Volatile var touch_x = 0.0
//    @Volatile var touch_y = 0.0
//    @Volatile var touch_force = 0.0
//    @Volatile var trigger = 0.0
//    @Volatile var trigger_btn = false
//    @Volatile var trigger_cap = false
//    @Volatile var grip_pull = 0.0
//    @Volatile var grip_force = 0.0
//
//    //skeletal
//    @Volatile var flexions = DoubleArray(20) { 0.0 }
//    @Volatile var splays = DoubleArray(5) { 0.0 }
//
//    //actions (will change!)
//    @Volatile var volUpAction = HardwareAction.NONE
//    @Volatile var volDownAction = HardwareAction.NONE
//    lateinit var sharedPrefs: android.content.SharedPreferences
//
//    //physical buttons-----------------------------------------------------------------------------------
////    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
////        when (keyCode) {
////            KeyEvent.KEYCODE_VOLUME_DOWN -> {
////                grip_pull = 1.0
////                grip_cap = true
////                return true
////            }
////            KeyEvent.KEYCODE_VOLUME_UP -> {
////                trigger = 1.0
////                trigger_btn = true
////                return true
////            }
////            //cant use power :(
//////            KeyEvent.KEYCODE_POWER -> {
//////                grip_pull = 1.0
//////                grip_cap = true
//////                return true
//////            }
////        }
////        return super.onKeyDown(keyCode, event)
////    }
////
////    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
////        when (keyCode) {
////            KeyEvent.KEYCODE_VOLUME_DOWN -> {
////                grip_pull = 0.0
////                grip_cap = false
////                return true
////            }
////            KeyEvent.KEYCODE_VOLUME_UP -> {
////                trigger = 0.0
////                trigger_btn = false
////                return true
////            }
////            //cant use power :(
//////            KeyEvent.KEYCODE_POWER -> {
//////                grip_pull = 0.0
//////                grip_cap = false
//////                return true
//////            }
////        }
////        return super.onKeyUp(keyCode, event)
////    }
//
//    //(will change!)
//    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
//        val action = when (keyCode) {
//            KeyEvent.KEYCODE_VOLUME_UP -> volUpAction
//            KeyEvent.KEYCODE_VOLUME_DOWN -> volDownAction
//            else -> return super.onKeyDown(keyCode, event)
//        }
//
//        when (action) {
//            HardwareAction.TRIGGER -> { trigger = 1.0;}
//            HardwareAction.GRIP_HOLD -> { grip_force = 1.0;}
//            HardwareAction.GRIP_TOGGLE -> {
//                if (event?.repeatCount == 0) {
//                    val newState = if (grip_force > 0.5) 0.0 else 1.0
//                    grip_force = newState
//                }
//            }
//            HardwareAction.NONE -> return super.onKeyDown(keyCode, event)
//        }
//        return true
//    }
//
//    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
//        val action = when (keyCode) {
//            KeyEvent.KEYCODE_VOLUME_UP -> volUpAction
//            KeyEvent.KEYCODE_VOLUME_DOWN -> volDownAction
//            else -> return super.onKeyUp(keyCode, event)
//        }
//
//        when (action) {
//            HardwareAction.TRIGGER -> { trigger = 0.0;}
//            HardwareAction.GRIP_HOLD -> { grip_force = 0.0;}
//            HardwareAction.GRIP_TOGGLE -> {}
//            HardwareAction.NONE -> return super.onKeyUp(keyCode, event)
//        }
//        return true
//    }
//
//    //physical buttons-----------------------------------------------------------------------------------
//
//    override fun onCreate(savedInstanceState: Bundle?) {
//        enableEdgeToEdge(
//            navigationBarStyle = SystemBarStyle.dark(scrim = Color.Black.toArgb())
//        )
//        super.onCreate(savedInstanceState)
//        setContent {
//            val context = LocalContext.current
//
//            var hasPermission by remember {
//                mutableStateOf(
//                    ContextCompat.checkSelfPermission(
//                        context, Manifest.permission.CAMERA
//                    ) == PackageManager.PERMISSION_GRANTED
//                )
//            }
//
//            val view = LocalView.current
//            SideEffect {
//                val window = (view.context as? ComponentActivity)?.window ?: return@SideEffect
//                val controller = WindowCompat.getInsetsController(window, view)
//                controller.hide(WindowInsetsCompat.Type.systemBars())
//                controller.systemBarsBehavior =
//                    WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
//            }
//
//            val launcher = rememberLauncherForActivityResult(
//                ActivityResultContracts.RequestPermission()
//            ) { granted -> hasPermission = granted }
//
//            LaunchedEffect(Unit) {
//                if (!hasPermission) launcher.launch(Manifest.permission.CAMERA)
//            }
//
//            if (hasPermission) {
//                Box(modifier = Modifier.fillMaxSize()) {
//                    AndroidView(
//                        modifier = Modifier.fillMaxSize(),
//                        factory = { ctx ->
//                            GLSurfaceView(ctx).also { view ->
//                                glSurfaceView = view
//                                view.preserveEGLContextOnPause = true
//                                view.setEGLContextClientVersion(2)
//                                val r = ArRenderer(this@MainActivity)
//                                renderer = r
//                                view.setRenderer(r)
//                                view.renderMode = GLSurfaceView.RENDERMODE_CONTINUOUSLY
//                            }
//                        }
//                    )
//                    AROverlayUI(activity = this@MainActivity)
//                }
//            } else {
//                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
//                    Text("Camera permission required", color = Color.White)
//                }
//            }
//
//            sharedPrefs = getSharedPreferences("GlassVrSettings", MODE_PRIVATE)
//            volUpAction = HardwareAction.valueOf(sharedPrefs.getString("volUp", HardwareAction.NONE.name)!!)
//            volDownAction = HardwareAction.valueOf(sharedPrefs.getString("volDown", HardwareAction.NONE.name)!!)
//
//        }
//    }
//
//    //reset session-----------------------------------------------------------------------------------
////fun resetSession(isStreaming: Boolean) {
////    if (!isStreaming) return
////
////    glSurfaceView.queueEvent {
////        try {
////            val textureId = renderer?.cameraTextureId?.get(0) ?: return@queueEvent
////            arSessionState.value?.close()
////            arSessionState.value = null
////            poseReady = false
////
////            resetFramesRemaining = 10
////
////            val newSession = Session(this@MainActivity).apply {
////                val config = Config(this)
////                config.updateMode = Config.UpdateMode.LATEST_CAMERA_IMAGE
////                configure(config)
////                setCameraTextureName(textureId)
////                resume()
////            }
////            arSessionState.value = newSession
////        } catch (e: Exception) {
////            e.printStackTrace()
////        }
////    }
////}
//    fun resetSession(isStreaming: Boolean) {
//        if (!isStreaming) return
//
//        glSurfaceView.queueEvent {
//            try {
//                // Detach frees the anchor from native tracking memory safely
//                originAnchor?.detach()
//                originAnchor = null
//                poseReady = false
//
//                resetFramesRemaining = 10
//
//            } catch (e: Exception) {
//                e.printStackTrace()
//            }
//        }
//    }
//    override fun onResume() {
//        super.onResume()
//        if (::glSurfaceView.isInitialized) glSurfaceView.onResume()
//    }
//
//    override fun onPause() {
//        super.onPause()
//        if (::glSurfaceView.isInitialized) glSurfaceView.onPause()
//        arSessionState.value?.pause()
//    }
//
//    override fun onDestroy() {
//        super.onDestroy()
//        arSessionState.value?.close()
//        arSessionState.value = null
//    }
//}
////gl idk-----------------------------------------------------------------------------------
//class ArRenderer(private val activity: MainActivity) : GLSurfaceView.Renderer {
//
//    val cameraTextureId = IntArray(1)
//
//    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
//        GLES20.glGenTextures(1, cameraTextureId, 0)
//        GLES20.glBindTexture(0x8D65, cameraTextureId[0])
//        GLES20.glTexParameteri(0x8D65, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
//        GLES20.glTexParameteri(0x8D65, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
//        GLES20.glTexParameteri(0x8D65, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_NEAREST)
//        GLES20.glTexParameteri(0x8D65, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_NEAREST)
//    }
//
//    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
//        GLES20.glViewport(0, 0, width, height)
//        activity.arSessionState.value?.setDisplayGeometry(0, width, height)
//    }
//
//    //    override fun onDrawFrame(gl: GL10?) {
////        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
////        val session = activity.arSessionState.value ?: return
////        try {
////            val frame: Frame = session.update()
////            val camera = frame.camera
////            if (camera.trackingState == TrackingState.TRACKING) {
////                val pose = camera.pose
////                activity.latestTx = pose.tx().toDouble()
////                activity.latestTy = pose.ty().toDouble()
////                activity.latestTz = pose.tz().toDouble()
////                activity.latestQw = pose.qw().toDouble()
////                activity.latestQx = pose.qx().toDouble()
////                activity.latestQy = pose.qy().toDouble()
////                activity.latestQz = pose.qz().toDouble()
////                activity.poseReady = true
////            }
////        } catch (e: Exception) {
////            e.printStackTrace()
////        }
////    }
//    override fun onDrawFrame(gl: GL10?) {
//        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
//        val session = activity.arSessionState.value ?: return
//
//        try {
//            val frame: Frame = session.update()
//            val camera = frame.camera
//
//            if (camera.trackingState == TrackingState.TRACKING) {
//                // Create the origin anchor on the first valid frame (or after a reset).
//                // Only capture yaw — pitch and roll come through correctly from the phone
//                // already, so we don't want the anchor to cancel them out.
//                // Extract yaw-only quaternion: project onto the Y-axis rotation and renormalize.
//                if (activity.originAnchor == null) {
//                    val cp = camera.pose
//                    val qw = cp.qw(); val qy = cp.qy()
//                    // Yaw-only quat around Y axis: keep only the w and y components, zero x and z
//                    val len = Math.sqrt((qw * qw + qy * qy).toDouble()).toFloat()
//                    val yawW = if (len > 0.0001f) qw / len else 1f
//                    val yawY = if (len > 0.0001f) qy / len else 0f
//                    val yawOnlyPose = com.google.ar.core.Pose(
//                        floatArrayOf(cp.tx(), cp.ty(), cp.tz()),
//                        floatArrayOf(0f, yawY, 0f, yawW)  // ARCore Pose quat order: x,y,z,w
//                    )
//                    activity.originAnchor = session.createAnchor(yawOnlyPose)
//                }
//
//                val anchor = activity.originAnchor ?: return
//
//                // All pose data (position + rotation) is now in the corrected frame
//                val relativePose = anchor.pose.inverse().compose(camera.pose)
//
//                activity.latestTx = relativePose.tx().toDouble()
//                activity.latestTy = relativePose.ty().toDouble()
//                activity.latestTz = relativePose.tz().toDouble()
//                activity.latestQw = relativePose.qw().toDouble()
//                activity.latestQx = relativePose.qx().toDouble()
//                activity.latestQy = relativePose.qy().toDouble()
//                activity.latestQz = relativePose.qz().toDouble()
//
//                activity.poseReady = true
//            }
//        } catch (e: Exception) {
//            e.printStackTrace()
//        }
//    }
//
//}
//fun quatMul(
//    qw: Double, qx: Double, qy: Double, qz: Double,
//    pw: Double, px: Double, py: Double, pz: Double
//): DoubleArray = doubleArrayOf(
//    qw*pw - qx*px - qy*py - qz*pz,
//    qw*px + qx*pw + qy*pz - qz*py,
//    qw*py - qx*pz + qy*pw + qz*px,
//    qw*pz + qx*py - qy*px + qz*pw
//)
//
////enums-----------------------------------------------------------------------------------
//enum class TouchUIMode(val label: String) {
//    NONE("None"),
//    HEADSET("Browser"),
//    INDEX_RIGHT("Index Right"),//,
//    INDEX_LEFT("Index Left"),
//    //INDEX_SKELETAL("Index Skeletal")
//    //INDEX_CONTROLLER("Index Controller")
//}
//
//enum class HardwareAction(val label: String) {
//    NONE("none"),
//    TRIGGER("trigger"),
//    GRIP_HOLD("grip(hold)"),
//    GRIP_TOGGLE("grip(toggle)")
//}
////enums-----------------------------------------------------------------------------------
//
////ui-----------------------------------------------------------------------------------
//@OptIn(ExperimentalMaterial3Api::class)
//@Composable
//fun AROverlayUI(activity: MainActivity) {
//    var currentPresetTrigger by remember { mutableStateOf("pass") }
//
//    val context = LocalContext.current
//    val prefs = remember { context.getSharedPreferences("ar_settings", Context.MODE_PRIVATE) }
//    val configuration = LocalConfiguration.current
//    val isLandscape = configuration.screenWidthDp > configuration.screenHeightDp
//
//    //persistent
//    //todo: add offsets in ui
//    var pitchOffset by remember {
//        mutableStateOf(prefs.getFloat("PitchOffset", -90.0f).toDouble())
//    }
//    LaunchedEffect(pitchOffset) {
//        activity.PitchOffset = pitchOffset
//        prefs.edit().putFloat("PitchOffset", pitchOffset.toFloat()).apply()
//    }
//
//    var volUpState by remember {
//        mutableStateOf(HardwareAction.valueOf(prefs.getString("volUp", HardwareAction.NONE.name) ?: HardwareAction.NONE.name))
//    }
//    var volDownState by remember {
//        mutableStateOf(HardwareAction.valueOf(prefs.getString("volDown", HardwareAction.NONE.name) ?: HardwareAction.NONE.name))
//    }
//    var volUpDropdownExpanded by remember { mutableStateOf(false) }
//    var volDownDropdownExpanded by remember { mutableStateOf(false) }
//    LaunchedEffect(volUpState) {
//        prefs.edit().putString("volUp", volUpState.name).apply()
//        activity.volUpAction = volUpState // Keep the activity updated
//    }
//    LaunchedEffect(volDownState) {
//        prefs.edit().putString("volDown", volDownState.name).apply()
//        activity.volDownAction = volDownState // Keep the activity updated
//    }
//
//    var ipAddress by remember { mutableStateOf(prefs.getString("ip", null) ?: "192.168.50.83") }
//    LaunchedEffect(ipAddress) { prefs.edit().putString("ip", ipAddress).apply() }
//
//    var port by remember { mutableStateOf(prefs.getString("port", null) ?: "9001") }
//    LaunchedEffect(port) { prefs.edit().putString("port", port).apply() }
//
//    var isVertical by remember { mutableStateOf(prefs.getBoolean("vertical", false)) }
//    LaunchedEffect(isVertical) {
//        activity.isVertical = isVertical; prefs.edit().putBoolean("vertical", isVertical).apply()
//    }
//
//    var isStreaming by remember { mutableStateOf(prefs.getBoolean("streaming", false)) }
//    LaunchedEffect(isStreaming) { prefs.edit().putBoolean("streaming", isStreaming).apply() }
//
//    var touchUIMode by remember {
//        mutableStateOf(
//            TouchUIMode.valueOf(
//                prefs.getString("touch_ui", TouchUIMode.NONE.name) ?: TouchUIMode.NONE.name
//            )
//        )
//    }
//    LaunchedEffect(touchUIMode) { prefs.edit().putString("touch_ui", touchUIMode.name).apply() }
//
//    var browserUrl by remember {
//        mutableStateOf(
//            prefs.getString("browser_url", null) ?: "192.168.50.83:9999"
//        )
//    }
//    LaunchedEffect(browserUrl) { prefs.edit().putString("browser_url", browserUrl).apply() }
//
//    var settingsExpanded by remember { mutableStateOf(false) }
//    var touchUIDropdownExpanded by remember { mutableStateOf(false) }
//
//    LaunchedEffect(Unit) {
//        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
//            var listenSocket: DatagramSocket? = null
//            try {
//                listenSocket = DatagramSocket(9002).apply { broadcast = true }
//                val buffer = ByteArray(256)
//                val packet = DatagramPacket(buffer, buffer.size)
//                while (true) {
//                    listenSocket.receive(packet)
//                    val msg = String(packet.data, 0, packet.length, Charsets.UTF_8).trim()
//                    if (msg == "RESET") {
//                        activity.resetSession(isStreaming = isStreaming)
//                    }
//                }
//            } catch (e: Exception) {
//                e.printStackTrace()
//            } finally {
//                listenSocket?.close()
//            }
//        }
//    }
//
//    LaunchedEffect(isStreaming) {
//        if (isStreaming) {
//            activity.glSurfaceView.queueEvent {
//                try {
//                    if (activity.arSessionState.value == null) {
//                        val textureId = activity.renderer?.cameraTextureId?.get(0) ?: 0
//                        val session = Session(activity).apply {
//                            val config = Config(this)
//                            config.updateMode = Config.UpdateMode.LATEST_CAMERA_IMAGE
//                            configure(config)
//                            setCameraTextureName(textureId)
//                            resume()
//                        }
//                        activity.arSessionState.value = session
//                    } else {
//                        activity.arSessionState.value?.resume()
//                    }
//                } catch (e: Exception) {
//                    e.printStackTrace()
//                }
//            }
//        } else {
//            activity.glSurfaceView.queueEvent {
//                try {
//                    activity.arSessionState.value?.pause()
//                    activity.arSessionState.value?.close()
//                    activity.arSessionState.value = null
//                    activity.poseReady = false
//                } catch (e: Exception) {
//                    e.printStackTrace()
//                }
//            }
//        }
//    }
//
//    LaunchedEffect(isStreaming) {
//        if (!isStreaming) return@LaunchedEffect
//        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
//            val socket = DatagramSocket()
//            val address = InetAddress.getByName(ipAddress)
//            val portInt = port.toIntOrNull() ?: 9001
//            val posBuffer = ByteBuffer.allocate(25).order(ByteOrder.LITTLE_ENDIAN)
//            val rotBuffer = ByteBuffer.allocate(33).order(ByteOrder.LITTLE_ENDIAN)
//            val extraBuffer = ByteBuffer.allocate(2).order(ByteOrder.LITTLE_ENDIAN)
//            val s = sin(Math.PI / 4)
//            val c = cos(Math.PI / 4)
//
//            //input: 'c' (1) + 12'?' (12) + 8'd' (64) = 77 bytes
//            val inputBuffer = ByteBuffer.allocate(77).order(ByteOrder.LITTLE_ENDIAN)
//            //skeletal: 'c' (1) + 25'd' (200) = 201 bytes
//            val skeletalBuffer = ByteBuffer.allocate(201).order(ByteOrder.LITTLE_ENDIAN)
//
//            //send data-----------------------------------------------------------------------------------
//            while (isStreaming) {
//                val tx = activity.latestTx;
//                val ty = activity.latestTy;
//                val tz = activity.latestTz
//                var qw = activity.latestQw;
//                var qx = activity.latestQx
//                var qy = activity.latestQy;
//                var qz = activity.latestQz
//
//                if (activity.isVertical) {
//                    val r = quatMul(qw, qx, qy, qz, c, 0.0, 0.0, -s)
//                    val pOff = Math.toRadians(pitchOffset);
//                    val rOff = Math.toRadians(180.0)
//                    val cp = cos(pOff * 0.5);
//                    val sp = sin(pOff * 0.5)
//                    val cr = cos(rOff * 0.5);
//                    val sr = sin(rOff * 0.5)
//                    val finalR =
//                        quatMul(r[0], r[1], r[2], r[3], cp * cr, sp * cr, -sp * sr, cp * sr)
//                    qw = finalR[0]; qx = finalR[1]; qy = finalR[2]; qz = finalR[3]
//                }
//
//                //extra
//                extraBuffer.clear()
//                extraBuffer.put('E'.code.toByte())
//                val isResetting = activity.resetFramesRemaining > 0
//                extraBuffer.put(if (isResetting) 1.toByte() else 0.toByte())
//                socket.send(
//                    DatagramPacket(
//                        extraBuffer.array(),
//                        extraBuffer.capacity(),
//                        address,
//                        portInt
//                    )
//                )
//                if (activity.resetFramesRemaining > 0) {
//                    activity.resetFramesRemaining--
//                }
//
//                //position
//                posBuffer.clear()
//                posBuffer.put('P'.code.toByte())
//                posBuffer.putDouble(tx); posBuffer.putDouble(ty); posBuffer.putDouble(tz)
//                socket.send(
//                    DatagramPacket(
//                        posBuffer.array(),
//                        posBuffer.capacity(),
//                        address,
//                        portInt
//                    )
//                )
//
//                //rotation
//                rotBuffer.clear()
//                rotBuffer.put('R'.code.toByte())
//                rotBuffer.putDouble(qw); rotBuffer.putDouble(qx)
//                rotBuffer.putDouble(qy); rotBuffer.putDouble(qz)
//                socket.send(
//                    DatagramPacket(
//                        rotBuffer.array(),
//                        rotBuffer.capacity(),
//                        address,
//                        portInt
//                    )
//                )
//
//                //input
//                inputBuffer.clear()
//                inputBuffer.put('I'.code.toByte())
//
//                //unused failsafe
//                activity.a_cap = activity.a
//                activity.b_cap = activity.b
//                activity.system_cap = activity.system
//
//                if (activity.trigger > 0.1){
//                    activity.trigger_cap = true
//                    activity.trigger_btn = true
//                }else{
//                    activity.trigger_cap = false
//                    activity.trigger_btn = false
//                }
//
//                if (activity.touch_x != 0.0 || activity.touch_y != 0.0 || activity.touch_force > 0.1){
//                    activity.touch_cap = true
//                }else{
//                    activity.touch_cap = false
//                }
//
//                if (activity.joy_x != 0.0 || activity.joy_y != 0.0){
//                    activity.joy_cap = true
//                }else{
//                    activity.joy_cap = false
//                }
//
//                if (activity.grip_force > 0.1){
//                    activity.grip_pull = 1.0
//                    activity.grip_cap = true
//                }else{
//                    activity.grip_pull = 0.0
//                    activity.grip_cap = false
//                }
//                //unused failsafe
//
//                val buttons = booleanArrayOf(
//                    activity.a, activity.b, activity.system, activity.joy_btn, activity.trigger_btn,
//                    activity.a_cap, activity.b_cap, activity.system_cap, activity.joy_cap,
//                    activity.trigger_cap, activity.touch_cap, activity.grip_cap
//                )
//                for (btn in buttons) inputBuffer.put(if (btn) 1.toByte() else 0.toByte())
//
//                inputBuffer.putDouble(activity.joy_x); inputBuffer.putDouble(activity.joy_y)
//                inputBuffer.putDouble(activity.touch_x); inputBuffer.putDouble(activity.touch_y)
//                inputBuffer.putDouble(activity.trigger); inputBuffer.putDouble(activity.touch_force)
//                inputBuffer.putDouble(activity.grip_pull); inputBuffer.putDouble(activity.grip_force)
//                socket.send(
//                    DatagramPacket(
//                        inputBuffer.array(),
//                        inputBuffer.position(),
//                        address,
//                        portInt
//                    )
//                )
//
//                //skeletal
//                skeletalBuffer.clear()
//                skeletalBuffer.put('S'.code.toByte())
//                val isHandActive = activity.joy_x != 0.0 || activity.joy_y != 0.0 ||
//                        activity.joy_btn || activity.touch_x != 0.0 ||
//                        activity.touch_y != 0.0 || activity.touch_force != 0.0
//                activity.flexions[0] = if (isHandActive) 1.0 else 0.0
//
//                if (activity.trigger > 0.1) {
//                    activity.flexions[4] = 1.0
//                } else {
//                    activity.flexions[4] = 0.0
//                }
//
//                if (activity.grip_cap) {
//                    activity.flexions[8] = 1.0
//                    activity.flexions[12] = 1.0
//                    activity.flexions[16] = 1.0
//                } else {
//                    activity.flexions[8] = 0.0
//                    activity.flexions[12] = 0.0
//                    activity.flexions[16] = 0.0
//                }
//
//                for (f in activity.flexions) skeletalBuffer.putDouble(f)
//                for (s in activity.splays) skeletalBuffer.putDouble(s)
//                socket.send(
//                    DatagramPacket(
//                        skeletalBuffer.array(),
//                        skeletalBuffer.position(),
//                        address,
//                        portInt
//                    )
//                )
//
//                Thread.sleep(1)
//            }
//            socket.close()
//        }
//    }
//
//    //bowser-----------------------------------------------------------------------------------
//    Box(modifier = Modifier.fillMaxSize()) {
//        if (touchUIMode == TouchUIMode.HEADSET) {
//            AndroidView(
//                modifier = Modifier.fillMaxSize(),
//                factory = { ctx ->
//                    WebView(ctx).apply {
//                        layoutParams = ViewGroup.LayoutParams(
//                            ViewGroup.LayoutParams.MATCH_PARENT,
//                            ViewGroup.LayoutParams.MATCH_PARENT
//                        )
//                        webViewClient = object : WebViewClient() {
//                            override fun onReceivedSslError(
//                                view: WebView,
//                                handler: android.webkit.SslErrorHandler,
//                                error: android.net.http.SslError
//                            ) {
//                                handler.proceed()
//                            }
//                        }
//                        settings.javaScriptEnabled = true
//                        settings.domStorageEnabled = true
//                        loadUrl(browserUrl)
//                    }
//                }
//            )
//        }
//
//        //index right-----------------------------------------------------------------------------------
//        if (touchUIMode == TouchUIMode.INDEX_RIGHT) {
//            Box(modifier = Modifier.fillMaxSize()) {
//                Column(
//                    modifier = Modifier
//                        .align(Alignment.TopEnd)
//                        .padding(top = 230.dp, end = 0.dp),
//                    horizontalAlignment = Alignment.End,
//                    verticalArrangement = Arrangement.spacedBy(0.dp)
//                ) {
//                    Row(
//                        horizontalArrangement = Arrangement.spacedBy(8.dp),
//                        modifier = Modifier.padding(end = 8.dp)
//                    ) {
//                        var isSystemPressing by remember { mutableStateOf(false) }
//                        Box(
//                            modifier = Modifier
//                                .width(300.dp)
//                                .height(100.dp)
//                                .background(Color(0xFF37474F), shape = RoundedCornerShape(14.dp))
//                                .pointerInput(Unit) {
//                                    detectTapGestures(onTap = {
//                                        activity.resetSession(isStreaming = isStreaming)
//                                    })
//                                },
//                            contentAlignment = Alignment.Center
//                        ) {
//                            Text(
//                                "↺ reset",
//                                color = Color.White,
//                                fontWeight = FontWeight.Bold,
//                                fontSize = 16.sp
//                            )
//                        }
//                        Box(
//                            modifier = Modifier
//                                .width(100.dp)
//                                .height(100.dp)
//                                .background(
//                                    if (isSystemPressing) Color(0xFF6A1B9A) else Color(0xFF3A0060),
//                                    shape = RoundedCornerShape(14.dp)
//                                )
//                                .pointerInput(Unit) {
//                                    detectTapGestures(onPress = {
//                                        isSystemPressing = true
//                                        activity.system = true
//                                        tryAwaitRelease()
//                                        isSystemPressing = false
//                                        activity.system = false
//                                    })
//                                },
//                            contentAlignment = Alignment.Center
//                        ) {
//                            Text(
//                                "SYS",
//                                color = Color.White,
//                                fontWeight = FontWeight.Bold,
//                                fontSize = 16.sp
//                            )
//                        }
//                    }
//                }
//                Column(
//                    modifier = Modifier.align(Alignment.CenterEnd),
//                    horizontalAlignment = Alignment.CenterHorizontally,
//                    verticalArrangement = Arrangement.spacedBy(16.dp),
//                ) {
//                    var joystickOffset by remember { mutableStateOf(Offset.Zero) }
//                    val maxRadius = 80.dp
//                    val maxRadiusPx = with(LocalDensity.current) { maxRadius.toPx() }
//
//                    Box(
//                        modifier = Modifier
//                            .size(160.dp)
//                            .background(Color.DarkGray.copy(alpha = 0.6f), shape = CircleShape),
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Box(
//                            modifier = Modifier
//                                .size(200.dp)
//                                .pointerInput(Unit) {
//                                    detectDragGestures(
//                                        onDragEnd = {
//                                            joystickOffset = Offset.Zero
//                                            activity.joy_x = 0.0
//                                            activity.joy_y = 0.0
//                                        },
//                                        onDragCancel = {
//                                            joystickOffset = Offset.Zero
//                                            activity.joy_x = 0.0
//                                            activity.joy_y = 0.0
//                                        },
//                                        onDrag = { change, dragAmount ->
//                                            change.consume()
//                                            val newOffset = joystickOffset + dragAmount
//                                            val distance = newOffset.getDistance()
//                                            joystickOffset = if (distance <= maxRadiusPx) newOffset
//                                            else newOffset / distance * maxRadiusPx
//                                            activity.joy_x =
//                                                (joystickOffset.x / maxRadiusPx).toDouble()
//                                            activity.joy_y =
//                                                -(joystickOffset.y / maxRadiusPx).toDouble()
//                                        }
//                                    )
//                                }
//                        )
//                        Box(
//                            modifier = Modifier
//                                .offset {
//                                    IntOffset(
//                                        joystickOffset.x.roundToInt(),
//                                        joystickOffset.y.roundToInt()
//                                    )
//                                }
//                                .size(80.dp)
//                                .background(Color(0xFF78909C), shape = CircleShape)
//                        )
//                    }
//
//                    Box(
//                        modifier = Modifier
//                            .size(110.dp)
//                            .background(Color(0xFF37474F), shape = RoundedCornerShape(20.dp))
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    activity.joy_btn = true; tryAwaitRelease(); activity.joy_btn =
//                                    false
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "JOY",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 24.sp
//                        )
//                    }
//                }
//                Column(
//                    modifier = Modifier.align(Alignment.Center),
//                    horizontalAlignment = Alignment.CenterHorizontally,
//                    verticalArrangement = Arrangement.spacedBy(14.dp)
//                ) {
//                    var isTouching by remember { mutableStateOf(false) }
//                    Box(
//                        modifier = Modifier
//                            .width(120.dp)
//                            .height(220.dp)
//                            .background(
//                                if (isTouching) Color(0xFF455A64) else Color(0xFF263238),
//                                shape = RoundedCornerShape(16.dp)
//                            )
//                            .pointerInput(Unit) {
//                                awaitPointerEventScope {
//                                    while (true) {
//                                        val event = awaitPointerEvent()
//                                        val pointer = event.changes.firstOrNull()
//                                        if (pointer != null && pointer.pressed) {
//                                            isTouching = true
//                                            activity.touch_cap = true
//                                            val s = this.size
//                                            activity.touch_x =
//                                                ((pointer.position.x / s.width) * 2f - 1f).toDouble()
//                                                    .coerceIn(-1.0, 1.0)
//                                            activity.touch_y =
//                                                -((pointer.position.y / s.height) * 2f - 1f).toDouble()
//                                                    .coerceIn(-1.0, 1.0)
//                                            pointer.consume()
//                                        } else {
//                                            isTouching = false
//                                            activity.touch_cap = false
//                                            activity.touch_x = 0.0
//                                            activity.touch_y = 0.0
//                                        }
//                                    }
//                                }
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text("TOUCHPAD", color = Color.Gray, fontSize = 11.sp)
//                    }
//
//                    var isForcePressing by remember { mutableStateOf(false) }
//                    Box(
//                        modifier = Modifier
//                            .width(120.dp)
//                            .height(56.dp)
//                            .background(
//                                if (isForcePressing) Color(0xFF00897B) else Color(0xFF004D40),
//                                shape = RoundedCornerShape(14.dp)
//                            )
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    isForcePressing = true
//                                    activity.touch_force = 1.0
//                                    tryAwaitRelease()
//                                    isForcePressing = false
//                                    activity.touch_force = 0.0
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "FORCE",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 16.sp
//                        )
//                    }
//                }
//
//                Column(
//                    modifier = Modifier
//                        .align(Alignment.CenterStart)
//                        .padding(start = 0.dp),
//                    verticalArrangement = Arrangement.spacedBy(16.dp),
//                    horizontalAlignment = Alignment.CenterHorizontally
//                ) {
//                    Box(
//                        modifier = Modifier
//                            .size(130.dp)
//                            .background(Color(0xFFB71C1C), shape = RoundedCornerShape(20.dp))
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    activity.b = true; tryAwaitRelease(); activity.b = false
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "B",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 36.sp
//                        )
//                    }
//
//                    Box(
//                        modifier = Modifier
//                            .size(130.dp)
//                            .background(Color(0xFF1565C0), shape = RoundedCornerShape(20.dp))
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    activity.a = true; tryAwaitRelease(); activity.a = false
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "A",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 36.sp
//                        )
//                    }
//                }
//
//                Column(
//                    modifier = Modifier
//                        .align(Alignment.BottomCenter)
//                        .padding(bottom = 16.dp),
//                    horizontalAlignment = Alignment.CenterHorizontally,
//                    verticalArrangement = Arrangement.spacedBy(10.dp)
//                ) {
//
//                    var isTriggerPressing by remember { mutableStateOf(false) }
//                    Box(
//                        modifier = Modifier
//                            .fillMaxWidth()
//                            .padding(horizontal = 32.dp)
//                            .height(150.dp)
//                            .background(
//                                if (isTriggerPressing) Color(0xFFFF6F00) else Color(0xFF7B3F00),
//                                shape = RoundedCornerShape(16.dp)
//                            )
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    isTriggerPressing = true
//                                    activity.trigger = 1.0
//                                    tryAwaitRelease()
//                                    isTriggerPressing = false
//                                    activity.trigger = 0.0
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "TRIGGER",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 20.sp
//                        )
//                    }
//
//                    Row(
//                        modifier = Modifier
//                            .fillMaxWidth()
//                            .padding(horizontal = 32.dp),
//                        horizontalArrangement = Arrangement.spacedBy(12.dp)
//                    ) {
//
//                        var isGripToggled by remember { mutableStateOf(false) }
//                        Box(
//                            modifier = Modifier
//                                .weight(1f)
//                                .height(150.dp)
//                                .background(
//                                    if (isGripToggled) Color(0xFF558B2F) else Color(0xFF2E4A1A),
//                                    shape = RoundedCornerShape(16.dp)
//                                )
//                                .pointerInput(Unit) {
//                                    detectTapGestures(
//                                        onTap = {
//                                            isGripToggled = !isGripToggled
//                                            activity.grip_force = if (isGripToggled) 1.0 else 0.0
//                                        }
//                                    )
//                                },
//                            contentAlignment = Alignment.Center
//                        ) {
//                            Text(
//                                if (isGripToggled) "GRIP\nON" else "GRIP\nOFF",
//                                color = Color.White,
//                                fontWeight = FontWeight.Bold,
//                                fontSize = 16.sp
//                            )
//                        }
//
//                        var isGripHolding by remember { mutableStateOf(false) }
//                        Box(
//                            modifier = Modifier
//                                .weight(1f)
//                                .height(150.dp)
//                                .background(
//                                    if (isGripHolding) Color(0xFF558B2F) else Color(0xFF2E4A1A),
//                                    shape = RoundedCornerShape(16.dp)
//                                )
//                                .pointerInput(isGripToggled) {
//                                    detectTapGestures(onPress = {
//                                        isGripHolding = true
//                                        activity.grip_force = if (isGripToggled) 0.0 else 1.0
//                                        tryAwaitRelease()
//                                        isGripHolding = false
//                                        activity.grip_force = if (isGripToggled) 1.0 else 0.0
//                                    })
//                                },
//                            contentAlignment = Alignment.Center
//                        ) {
//                            Text(
//                                "GRIP\n(hold)",
//                                color = Color.White,
//                                fontWeight = FontWeight.Bold,
//                                fontSize = 16.sp
//                            )
//                        }
//                    }
//                }
//            }
//        }
//        //index left-----------------------------------------------------------------------------------
//        if (touchUIMode == TouchUIMode.INDEX_LEFT) {
//            Box(modifier = Modifier.fillMaxSize()) {
//
//                Column(
//                    modifier = Modifier
//                        .align(Alignment.TopStart)
//                        .padding(top = 230.dp, start = 0.dp),
//                    horizontalAlignment = Alignment.Start,
//                    verticalArrangement = Arrangement.spacedBy(0.dp)
//                ) {
//                    Row(
//                        horizontalArrangement = Arrangement.spacedBy(8.dp),
//                        modifier = Modifier.padding(start = 8.dp)
//                    ) {
//                        var isSystemPressing by remember { mutableStateOf(false) }
//                        Box(
//                            modifier = Modifier
//                                .width(100.dp)
//                                .height(100.dp)
//                                .background(
//                                    if (isSystemPressing) Color(0xFF6A1B9A) else Color(0xFF3A0060),
//                                    shape = RoundedCornerShape(14.dp)
//                                )
//                                .pointerInput(Unit) {
//                                    detectTapGestures(onPress = {
//                                        isSystemPressing = true
//                                        activity.system = true
//                                        tryAwaitRelease()
//                                        isSystemPressing = false
//                                        activity.system = false
//                                    })
//                                },
//                            contentAlignment = Alignment.Center
//                        ) {
//                            Text(
//                                "SYS",
//                                color = Color.White,
//                                fontWeight = FontWeight.Bold,
//                                fontSize = 16.sp
//                            )
//                        }
//                        Box(
//                            modifier = Modifier
//                                .width(300.dp)
//                                .height(100.dp)
//                                .background(Color(0xFF37474F), shape = RoundedCornerShape(14.dp))
//                                .pointerInput(Unit) {
//                                    detectTapGestures(onTap = {
//                                        activity.resetSession(isStreaming = isStreaming)
//                                    })
//                                },
//                            contentAlignment = Alignment.Center
//                        ) {
//                            Text(
//                                "↺ RESET",
//                                color = Color.White,
//                                fontWeight = FontWeight.Bold,
//                                fontSize = 16.sp
//                            )
//                        }
//                    }
//                }
//
//                Column(
//                    modifier = Modifier.align(Alignment.CenterStart),
//                    horizontalAlignment = Alignment.CenterHorizontally,
//                    verticalArrangement = Arrangement.spacedBy(16.dp),
//                ) {
//                    var joystickOffset by remember { mutableStateOf(Offset.Zero) }
//                    val maxRadius = 80.dp
//                    val maxRadiusPx = with(LocalDensity.current) { maxRadius.toPx() }
//
//                    Box(
//                        modifier = Modifier
//                            .size(160.dp)
//                            .background(Color.DarkGray.copy(alpha = 0.6f), shape = CircleShape),
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Box(
//                            modifier = Modifier
//                                .size(200.dp)
//                                .pointerInput(Unit) {
//                                    detectDragGestures(
//                                        onDragEnd = {
//                                            joystickOffset = Offset.Zero
//                                            activity.joy_x = 0.0
//                                            activity.joy_y = 0.0
//                                        },
//                                        onDragCancel = {
//                                            joystickOffset = Offset.Zero
//                                            activity.joy_x = 0.0
//                                            activity.joy_y = 0.0
//                                        },
//                                        onDrag = { change, dragAmount ->
//                                            change.consume()
//                                            val newOffset = joystickOffset + dragAmount
//                                            val distance = newOffset.getDistance()
//                                            joystickOffset = if (distance <= maxRadiusPx) newOffset
//                                            else newOffset / distance * maxRadiusPx
//                                            activity.joy_x =
//                                                (joystickOffset.x / maxRadiusPx).toDouble()
//                                            activity.joy_y =
//                                                -(joystickOffset.y / maxRadiusPx).toDouble()
//                                        }
//                                    )
//                                }
//                        )
//                        Box(
//                            modifier = Modifier
//                                .offset {
//                                    IntOffset(
//                                        joystickOffset.x.roundToInt(),
//                                        joystickOffset.y.roundToInt()
//                                    )
//                                }
//                                .size(80.dp)
//                                .background(Color(0xFF78909C), shape = CircleShape)
//                        )
//                    }
//
//                    Box(
//                        modifier = Modifier
//                            .size(110.dp)
//                            .background(Color(0xFF37474F), shape = RoundedCornerShape(20.dp))
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    activity.joy_btn = true; tryAwaitRelease(); activity.joy_btn =
//                                    false
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "JOY",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 24.sp
//                        )
//                    }
//                }
//
//                Column(
//                    modifier = Modifier.align(Alignment.Center),
//                    horizontalAlignment = Alignment.CenterHorizontally,
//                    verticalArrangement = Arrangement.spacedBy(14.dp)
//                ) {
//                    var isTouching by remember { mutableStateOf(false) }
//                    Box(
//                        modifier = Modifier
//                            .width(120.dp)
//                            .height(220.dp)
//                            .background(
//                                if (isTouching) Color(0xFF455A64) else Color(0xFF263238),
//                                shape = RoundedCornerShape(16.dp)
//                            )
//                            .pointerInput(Unit) {
//                                awaitPointerEventScope {
//                                    while (true) {
//                                        val event = awaitPointerEvent()
//                                        val pointer = event.changes.firstOrNull()
//                                        if (pointer != null && pointer.pressed) {
//                                            isTouching = true
//                                            activity.touch_cap = true
//                                            val s = this.size
//                                            activity.touch_x =
//                                                ((pointer.position.x / s.width) * 2f - 1f).toDouble()
//                                                    .coerceIn(-1.0, 1.0)
//                                            activity.touch_y =
//                                                -((pointer.position.y / s.height) * 2f - 1f).toDouble()
//                                                    .coerceIn(-1.0, 1.0)
//                                            pointer.consume()
//                                        } else {
//                                            isTouching = false
//                                            activity.touch_cap = false
//                                            activity.touch_x = 0.0
//                                            activity.touch_y = 0.0
//                                        }
//                                    }
//                                }
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text("TOUCHPAD", color = Color.Gray, fontSize = 11.sp)
//                    }
//
//                    var isForcePressing by remember { mutableStateOf(false) }
//                    Box(
//                        modifier = Modifier
//                            .width(120.dp)
//                            .height(56.dp)
//                            .background(
//                                if (isForcePressing) Color(0xFF00897B) else Color(0xFF004D40),
//                                shape = RoundedCornerShape(14.dp)
//                            )
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    isForcePressing = true
//                                    activity.touch_force = 1.0
//                                    tryAwaitRelease()
//                                    isForcePressing = false
//                                    activity.touch_force = 0.0
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "FORCE",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 16.sp
//                        )
//                    }
//                }
//
//                Column(
//                    modifier = Modifier
//                        .align(Alignment.CenterEnd)
//                        .padding(end = 0.dp),
//                    verticalArrangement = Arrangement.spacedBy(16.dp),
//                    horizontalAlignment = Alignment.CenterHorizontally
//                ) {
//                    Box(
//                        modifier = Modifier
//                            .size(130.dp)
//                            .background(Color(0xFFB71C1C), shape = RoundedCornerShape(20.dp))
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    activity.b = true; tryAwaitRelease(); activity.b = false
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "B",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 36.sp
//                        )
//                    }
//
//                    Box(
//                        modifier = Modifier
//                            .size(130.dp)
//                            .background(Color(0xFF1565C0), shape = RoundedCornerShape(20.dp))
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    activity.a = true; tryAwaitRelease(); activity.a = false
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "A",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 36.sp
//                        )
//                    }
//                }
//
//                Column(
//                    modifier = Modifier
//                        .align(Alignment.BottomCenter)
//                        .padding(bottom = 16.dp),
//                    horizontalAlignment = Alignment.CenterHorizontally,
//                    verticalArrangement = Arrangement.spacedBy(10.dp)
//                ) {
//                    var isTriggerPressing by remember { mutableStateOf(false) }
//                    Box(
//                        modifier = Modifier
//                            .fillMaxWidth()
//                            .padding(horizontal = 32.dp)
//                            .height(150.dp)
//                            .background(
//                                if (isTriggerPressing) Color(0xFFFF6F00) else Color(0xFF7B3F00),
//                                shape = RoundedCornerShape(16.dp)
//                            )
//                            .pointerInput(Unit) {
//                                detectTapGestures(onPress = {
//                                    isTriggerPressing = true
//                                    activity.trigger = 1.0
//                                    tryAwaitRelease()
//                                    isTriggerPressing = false
//                                    activity.trigger = 0.0
//                                })
//                            },
//                        contentAlignment = Alignment.Center
//                    ) {
//                        Text(
//                            "TRIGGER",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 20.sp
//                        )
//                    }
//
//                    Row(
//                        modifier = Modifier
//                            .fillMaxWidth()
//                            .padding(horizontal = 32.dp),
//                        horizontalArrangement = Arrangement.spacedBy(12.dp)
//                    ) {
//
//                        var isGripHolding by remember { mutableStateOf(false) }
//                        var isGripToggled by remember { mutableStateOf(false) }
//                        Box(
//                            modifier = Modifier
//                                .weight(1f)
//                                .height(150.dp)
//                                .background(
//                                    if (isGripHolding) Color(0xFF558B2F) else Color(0xFF2E4A1A),
//                                    shape = RoundedCornerShape(16.dp)
//                                )
//                                .pointerInput(isGripToggled) {
//                                    detectTapGestures(onPress = {
//                                        isGripHolding = true
//                                        activity.grip_force = if (isGripToggled) 0.0 else 1.0
//                                        tryAwaitRelease()
//                                        isGripHolding = false
//                                        activity.grip_force = if (isGripToggled) 1.0 else 0.0
//                                    })
//                                },
//                            contentAlignment = Alignment.Center
//                        ) {
//                            Text(
//                                "GRIP\n(hold)",
//                                color = Color.White,
//                                fontWeight = FontWeight.Bold,
//                                fontSize = 16.sp
//                            )
//                        }
//
//                        Box(
//                            modifier = Modifier
//                                .weight(1f)
//                                .height(150.dp)
//                                .background(
//                                    if (isGripToggled) Color(0xFF558B2F) else Color(0xFF2E4A1A),
//                                    shape = RoundedCornerShape(16.dp)
//                                )
//                                .pointerInput(Unit) {
//                                    detectTapGestures(
//                                        onTap = {
//                                            isGripToggled = !isGripToggled
//                                            activity.grip_force = if (isGripToggled) 1.0 else 0.0
//                                        }
//                                    )
//                                },
//                            contentAlignment = Alignment.Center
//                        ) {
//                            Text(
//                                if (isGripToggled) "GRIP\nON" else "GRIP\nOFF",
//                                color = Color.White,
//                                fontWeight = FontWeight.Bold,
//                                fontSize = 16.sp
//                            )
//                        }
//                    }
//                }
//            }
//        }
//        //index controller-----------------------------------------------------------------------
//        //if (touchUIMode == TouchUIMode.INDEX_CONTROLLER) {
//        if (true != true){
//            SuperButton(
//                id = "btn_A",
//                label = "A",
//                isActive = activity.a,
//                onToggle = { activity.a = it },
//                defaultX = 50f,
//                defaultY = 100f,
//                prefs = prefs,
//                activity = activity
//            )
//
//            SuperButton(
//                id = "btn_B",
//                label = "B",
//                isActive = activity.b,
//                onToggle = { activity.b = it },
//                defaultX = 150f,
//                defaultY = 100f,
//                prefs = prefs,
//                activity = activity
//            )
//
//            SuperButton(
//                id = "btn_SYS",
//                label = "SYS",
//                isActive = activity.system,
//                onToggle = { activity.system = it },
//                defaultX = 250f,
//                defaultY = 100f,
//                prefs = prefs,
//                activity = activity
//            )
//        }
//
//        //nav bar-----------------------------------------------------------------------------------
//        val uriHandler = LocalUriHandler.current
//        if (isLandscape) {
//            Column(
//                modifier = Modifier
//                    .fillMaxHeight()
//                    .width(32.dp)
//                    .background(Color.Black.copy(alpha = 0.55f))
//                    .padding(4.dp),
//                verticalArrangement = Arrangement.Top,
//                horizontalAlignment = Alignment.CenterHorizontally
//            ) {
//                IconTextButton(
//                    label = "⚙",
//                    modifier = Modifier.fillMaxWidth().height(64.dp),
//                    onClick = { settingsExpanded = !settingsExpanded }
//                )
//                Spacer(modifier = Modifier.height(4.dp))
//                RotatedResetButton(
//                    modifier = Modifier.weight(1f).fillMaxWidth(),
//                    onClick = { activity.resetSession(isStreaming = isStreaming) }
//                )
//            }
//        } else {
//            Row(
//                modifier = Modifier
//                    .fillMaxWidth()
//                    .wrapContentHeight()
//                    .background(Color.Black.copy(alpha = 0.55f))
//                    .padding(4.dp),
//                verticalAlignment = Alignment.CenterVertically
//            ) {
//                IconTextButton(
//                    label = "⚙",
//                    modifier = Modifier.size(64.dp),
//                    onClick = { settingsExpanded = !settingsExpanded }
//                )
//                Spacer(modifier = Modifier.width(4.dp))
//                Button(
//                    onClick = { activity.resetSession(isStreaming = isStreaming) },
//                    modifier = Modifier.weight(1f).height(64.dp),
//                    colors = ButtonDefaults.buttonColors(containerColor = Color.Gray),
//                    contentPadding = PaddingValues(0.dp),
//                    shape = MaterialTheme.shapes.small
//                ) {
//                    Text("↺", fontSize = 14.sp, fontWeight = FontWeight.Bold)
//                }
//            }
//        }
//        //settings card-----------------------------------------------------------------------------------
//        if (settingsExpanded) {
//            Box(
//                modifier = Modifier
//                    .fillMaxSize()
//                    .padding(top = 44.dp)
//            ) {
//                Card(
//                    modifier = Modifier
//                        .wrapContentSize()
//                        .padding(8.dp),
//                    colors = CardDefaults.cardColors(
//                        containerColor = Color(0xFF1A1A2E).copy(alpha = 0.95f)
//                    ),
//                    elevation = CardDefaults.cardElevation(8.dp)
//                ) {
//                    Column(
//                        modifier = Modifier
//                            .padding(16.dp)
//                            .verticalScroll(rememberScrollState())
//                            .widthIn(min = 260.dp, max = 340.dp)
//                    ) {
//                        Text(
//                            "Settings",
//                            color = Color.White,
//                            fontWeight = FontWeight.Bold,
//                            fontSize = 16.sp,
//                            modifier = Modifier.padding(bottom = 12.dp)
//                        )
//
//                        val displayMetrics = LocalContext.current.resources.displayMetrics
//                        val widthPx = displayMetrics.widthPixels
//                        val heightPx = displayMetrics.heightPixels
//                        val density = displayMetrics.density
//                        val widthDp = (widthPx / density).toInt()
//                        val heightDp = (heightPx / density).toInt()
//
//                        Text("Resolution", color = Color.Gray, fontSize = 11.sp)
//                        Text(
//                            "${widthPx} × ${heightPx} px  (${widthDp} × ${heightDp} dp)",
//                            color = Color.White,
//                            fontSize = 12.sp,
//                            modifier = Modifier.padding(bottom = 10.dp)
//                        )
//
//                        Text("Host IP", color = Color.Gray, fontSize = 11.sp)
//                        OutlinedTextField(
//                            value = ipAddress,
//                            onValueChange = { ipAddress = it },
//                            singleLine = true,
//                            colors = OutlinedTextFieldDefaults.colors(
//                                focusedTextColor = Color.White,
//                                unfocusedTextColor = Color.White,
//                                focusedBorderColor = Color(0xFF5C6BC0),
//                                unfocusedBorderColor = Color.Gray
//                            ),
//                            modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp)
//                        )
//
//                        Text("Port", color = Color.Gray, fontSize = 11.sp)
//                        OutlinedTextField(
//                            value = port,
//                            onValueChange = { newValue ->
//                                if (newValue.isEmpty() || newValue.all { it.isDigit() }) {
//                                    port = newValue
//                                }
//                            },
//                            singleLine = true,
//                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
//                            colors = OutlinedTextFieldDefaults.colors(
//                                focusedTextColor = Color.White,
//                                unfocusedTextColor = Color.White,
//                                focusedBorderColor = Color(0xFF5C6BC0),
//                                unfocusedBorderColor = Color.Gray
//                            ),
//                            modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp)
//                        )
//
//                        Row(
//                            verticalAlignment = Alignment.CenterVertically,
//                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
//                        ) {
//                            Checkbox(
//                                checked = isVertical,
//                                onCheckedChange = { isVertical = it },
//                                colors = CheckboxDefaults.colors(checkedColor = Color(0xFF5C6BC0))
//                            )
//                            Text(
//                                if (isVertical) "Vertical (portrait)" else "Horizontal (landscape)",
//                                color = Color.White,
//                                fontSize = 13.sp
//                            )
//                        }
//
//                        Row(
//                            verticalAlignment = Alignment.CenterVertically,
//                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
//                        ) {
//                            Checkbox(
//                                checked = isStreaming,
//                                onCheckedChange = { isStreaming = it },
//                                colors = CheckboxDefaults.colors(
//                                    checkedColor = Color(0xFF43A047),
//                                    uncheckedColor = Color.Gray
//                                )
//                            )
//                            Text(
//                                if (isStreaming) "Streaming ON" else "Streaming OFF",
//                                color = if (isStreaming) Color(0xFF81C784) else Color.White,
//                                fontSize = 13.sp
//                            )
//                        }
//
//                        Text("Vertical Pitch Offset(default -90.0)", color = Color.Gray, fontSize = 11.sp)
//                        OutlinedTextField(
//                            value = pitchOffset.toString(),
//                            onValueChange = { newValue: String ->
//                                if (newValue.isEmpty() || newValue == "-" || newValue.matches(Regex("-?\\d*\\.?\\d*"))) {
//                                    pitchOffset = newValue.toDoubleOrNull() ?: pitchOffset
//                                }
//                            },
//                            singleLine = true,
//                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text),
//                            colors = OutlinedTextFieldDefaults.colors(
//                                focusedTextColor = Color.White,
//                                unfocusedTextColor = Color.White,
//                                focusedBorderColor = Color(0xFF5C6BC0),
//                                unfocusedBorderColor = Color.Gray
//                            ),
//                            modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp)
//                        )
//
//                        Text("Browser URL", color = Color.Gray, fontSize = 11.sp)
//                        OutlinedTextField(
//                            value = browserUrl,
//                            onValueChange = { browserUrl = it },
//                            singleLine = true,
//                            colors = OutlinedTextFieldDefaults.colors(
//                                focusedTextColor = Color.White,
//                                unfocusedTextColor = Color.White,
//                                focusedBorderColor = Color(0xFF5C6BC0),
//                                unfocusedBorderColor = Color.Gray
//                            ),
//                            modifier = Modifier.fillMaxWidth()
//                                .padding(top = 4.dp, bottom = 10.dp)
//                        )
//
////                        HorizontalDivider(
////                            color = Color.Gray.copy(alpha = 0.3f),
////                            modifier = Modifier.padding(vertical = 4.dp)
////                        )
//
//                        Text(
//                            "Touch UI",
//                            color = Color.Gray,
//                            fontSize = 11.sp,
//                            modifier = Modifier.padding(bottom = 4.dp)
//                        )
//                        ExposedDropdownMenuBox(
//                            expanded = touchUIDropdownExpanded,
//                            onExpandedChange = { touchUIDropdownExpanded = it }
//                        ) {
//                            OutlinedTextField(
//                                value = touchUIMode.label,
//                                onValueChange = {},
//                                readOnly = true,
//                                trailingIcon = {
//                                    ExposedDropdownMenuDefaults.TrailingIcon(
//                                        expanded = touchUIDropdownExpanded
//                                    )
//                                },
//                                colors = OutlinedTextFieldDefaults.colors(
//                                    focusedTextColor = Color.White,
//                                    unfocusedTextColor = Color.White,
//                                    focusedBorderColor = Color(0xFF5C6BC0),
//                                    unfocusedBorderColor = Color.Gray
//                                ),
//                                modifier = Modifier.menuAnchor().fillMaxWidth()
//                            )
//                            ExposedDropdownMenu(
//                                expanded = touchUIDropdownExpanded,
//                                onDismissRequest = { touchUIDropdownExpanded = false },
//                                containerColor = Color(0xFF1A1A2E)
//                            ) {
//                                TouchUIMode.entries.forEach { mode ->
//                                    DropdownMenuItem(
//                                        text = { Text(mode.label, color = Color.White) },
//                                        onClick = {
//                                            touchUIMode = mode
//                                            touchUIDropdownExpanded = false
//                                        }
//                                    )
//                                }
//                            }
//                        }
//
//                        //readd later---------------------------------------------------------------
////                        Row(
////                            verticalAlignment = Alignment.CenterVertically,
////                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
////                        ) {
////                            Checkbox(
////                                checked = activity.InEdit,
////                                onCheckedChange = { activity.InEdit = it }, // Directly flips the main variable
////                                colors = CheckboxDefaults.colors(
////                                    checkedColor = Color(0xFF43A047),
////                                    uncheckedColor = Color.Gray
////                                )
////                            )
////                            Text(
////                                text = if (activity.InEdit) "Editing" else "Not Editing",
////                                color = if (activity.InEdit) Color(0xFF81C784) else Color.White,
////                                fontSize = 13.sp
////                            )
////                        }
//
////                        PresetLayoutComboBox(prefs = prefs, activity = activity)
//
//                        //readd later---------------------------------------------------------------
//
//                        Text("Volume Up Action", color = Color.Gray, fontSize = 11.sp, modifier = Modifier.padding(bottom = 4.dp))
//                        ExposedDropdownMenuBox(
//                            expanded = volUpDropdownExpanded,
//                            onExpandedChange = { volUpDropdownExpanded = it }
//                        ) {
//                            OutlinedTextField(
//                                value = volUpState.label,
//                                onValueChange = {},
//                                readOnly = true,
//                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = volUpDropdownExpanded) },
//                                colors = OutlinedTextFieldDefaults.colors(
//                                    focusedTextColor = Color.White, unfocusedTextColor = Color.White,
//                                    focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray
//                                ),
//                                modifier = Modifier.menuAnchor().fillMaxWidth()
//                            )
//                            ExposedDropdownMenu(
//                                expanded = volUpDropdownExpanded,
//                                onDismissRequest = { volUpDropdownExpanded = false },
//                                containerColor = Color(0xFF1A1A2E)
//                            ) {
//                                HardwareAction.entries.forEach { action ->
//                                    DropdownMenuItem(
//                                        text = { Text(action.label, color = Color.White) },
//                                        onClick = {
//                                            volUpState = action
//                                            activity.volUpAction = action
//                                            activity.sharedPrefs.edit().putString("volUp", action.name).apply()
//                                            volUpDropdownExpanded = false
//                                        }
//                                    )
//                                }
//                            }
//                        }
//                        Text("Volume Down Action", color = Color.Gray, fontSize = 11.sp, modifier = Modifier.padding(bottom = 4.dp))
//                        ExposedDropdownMenuBox(
//                            expanded = volDownDropdownExpanded,
//                            onExpandedChange = { volDownDropdownExpanded = it }
//                        ) {
//                            OutlinedTextField(
//                                value = volDownState.label,
//                                onValueChange = {},
//                                readOnly = true,
//                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = volDownDropdownExpanded) },
//                                colors = OutlinedTextFieldDefaults.colors(
//                                    focusedTextColor = Color.White, unfocusedTextColor = Color.White,
//                                    focusedBorderColor = Color(0xFF5C6BC0), unfocusedBorderColor = Color.Gray
//                                ),
//                                modifier = Modifier.menuAnchor().fillMaxWidth()
//                            )
//                            ExposedDropdownMenu(
//                                expanded = volDownDropdownExpanded,
//                                onDismissRequest = { volDownDropdownExpanded = false },
//                                containerColor = Color(0xFF1A1A2E)
//                            ) {
//                                HardwareAction.entries.forEach { action ->
//                                    DropdownMenuItem(
//                                        text = { Text(action.label, color = Color.White) },
//                                        onClick = {
//                                            volDownState = action
//                                            activity.volDownAction = action
//                                            activity.sharedPrefs.edit().putString("volDown", action.name).apply()
//                                            volDownDropdownExpanded = false
//                                        }
//                                    )
//                                }
//                            }
//                        }
//
//                        Text(
//                            "Made By: DaniXmir",
//                            color = Color.White,
//                            fontSize = 24.sp,
//                            modifier = Modifier.padding(bottom = 4.dp)
//                        )
//
//                        GifButton()
//
//                        Row {
//                            Text(
//                                text = "youtube!",
//                                color = Color(0xFF5C6BC0),
//                                fontSize = 22.sp,
//                                textDecoration = TextDecoration.Underline,
//                                modifier = Modifier
//                                    .clickable { uriHandler.openUri("https://www.youtube.com/") }
//                                    .padding(vertical = 4.dp)
//                            )
//                            Text(
//                                "   ",
//                                color = Color.White,
//                                fontSize = 24.sp,
//                                modifier = Modifier.padding(bottom = 4.dp)
//                            )
//                            Text(
//                                text = "github!",
//                                color = Color(0xFF5C6BC0),
//                                fontSize = 22.sp,
//                                textDecoration = TextDecoration.Underline,
//                                modifier = Modifier
//                                    .clickable { uriHandler.openUri("https://github.com/DaniXmir/GlassVr") }
//                                    .padding(vertical = 4.dp)
//                            )
//                            Text(
//                                "   ",
//                                color = Color.White,
//                                fontSize = 24.sp,
//                                modifier = Modifier.padding(bottom = 4.dp)
//                            )
//                            Text(
//                                text = "discord!",
//                                color = Color(0xFF5C6BC0),
//                                fontSize = 22.sp,
//                                textDecoration = TextDecoration.Underline,
//                                modifier = Modifier
//                                    .clickable { uriHandler.openUri("https://discord.com/invite/jyvWdKBpPj") }
//                                    .padding(vertical = 4.dp)
//                            )
//                        }
//                    }
//                }
//            }
//        }
//    }
//}
//
////composable buttons--------------------------------------------------------------------------------
////nav bar
//@Composable
//fun IconTextButton(
//    label: String,
//    onClick: () -> Unit,
//    modifier: Modifier = Modifier
//) {
//    Button(
//        onClick = onClick,
//        modifier = modifier,
//        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF37474F)),
//        contentPadding = PaddingValues(0.dp)
//    ) {
//        Text(label, fontSize = 16.sp)
//    }
//}
//
//@Composable
//fun RotatedResetButton(modifier: Modifier = Modifier, onClick: () -> Unit) {
//    Button(
//        onClick = onClick,
//        modifier = modifier,
//        colors = ButtonDefaults.buttonColors(containerColor = Color.Gray),
//        contentPadding = PaddingValues(0.dp),
//        shape = MaterialTheme.shapes.small
//    ) {
//        Text(
//            "↺",
//            fontSize = 20.sp,
//            fontWeight = FontWeight.Bold,
//            color = Color.White
//        )
//    }
//}
////extra
//@Composable
//fun GifButton() {
//    val context = LocalContext.current
//
//    AsyncImage(
//        model = ImageRequest.Builder(context)
//            .data(R.drawable.fix_anim)
//            .decoderFactory(GifDecoder.Factory())
//            .build(),
//        contentDescription = "Alert Button",
//        modifier = Modifier
//            .size(200.dp)
//            .clickable {
//                //2008 (Android 1.0)
//                val alertContext = ContextThemeWrapper(context, android.R.style.Theme_Dialog)
//
//                //2011 (Android 3.0/4.0)
//                //val alertContext = ContextThemeWrapper(context, android.R.style.Theme_Holo_Dialog)
//
//                //2012 (Android 4.0.3)
//                //val alertContext = ContextThemeWrapper(context, android.R.style.Theme_DeviceDefault_Dialog)
//
//                //2014 (Android 5.0)
//                //val alertContext = ContextThemeWrapper(context, android.R.style.Theme_Material_Dialog)
//
//                AlertDialog.Builder(alertContext)
//                    .setTitle(";P")
//                    .setMessage("OUCH!")
//                    .setPositiveButton("ok") { dialog, _ ->
//                        dialog.dismiss()
//                    }
//                    .create()
//                    .show()
//            }
//    )
//}
//
//@Composable
//fun Gif() {
//    AsyncImage(
//        model = ImageRequest.Builder(LocalContext.current)
//            .data(R.drawable.fix_anim)
//            .decoderFactory(GifDecoder.Factory())
//            .build(),
//        contentDescription = null,
//        modifier = Modifier.size(200.dp)
//    )
//}
//
////index layouts
//@OptIn(ExperimentalMaterial3Api::class)
//@Composable
//fun PresetLayoutComboBox(
//    prefs: android.content.SharedPreferences,
//    activity: MainActivity
//) {
//    val options = listOf("pass", "one")
//    var expanded by remember { mutableStateOf(false) }
//    var selectedOption by remember { mutableStateOf(options[0]) }
//
//    Box(modifier = Modifier.padding(vertical = 8.dp)) {
//        ExposedDropdownMenuBox(
//            expanded = expanded,
//            onExpandedChange = { expanded = it }
//        ) {
//            OutlinedTextField(
//                modifier = Modifier.menuAnchor().fillMaxWidth(),
//                readOnly = true,
//                value = selectedOption,
//                onValueChange = {},
//                label = { Text("Preset Layout", color = Color.White) },
//                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
//                colors = OutlinedTextFieldDefaults.colors(
//                    focusedTextColor = Color.White,
//                    unfocusedTextColor = Color.White,
//                    focusedBorderColor = Color(0xFF0288D1),
//                    unfocusedBorderColor = Color.Gray
//                )
//            )
//
//            ExposedDropdownMenu(
//                expanded = expanded,
//                onDismissRequest = { expanded = false }
//            ) {
//                options.forEach { option ->
//                    DropdownMenuItem(
//                        text = { Text(option) },
//                        onClick = {
//                            selectedOption = option
//                            expanded = false
//
//                            if (option == "one") {
//                                prefs.edit().apply {
//                                    // Including width/height so your resizable buttons don't break!
//                                    putFloat("btn_A_x", 100f)
//                                    putFloat("btn_A_y", 150f)
//                                    putFloat("btn_A_width", 80f)
//                                    putFloat("btn_A_height", 80f)
//
//                                    putFloat("btn_B_x", 250f)
//                                    putFloat("btn_B_y", 150f)
//                                    putFloat("btn_B_width", 80f)
//                                    putFloat("btn_B_height", 80f)
//
//                                    putFloat("btn_SYS_x", 400f)
//                                    putFloat("btn_SYS_y", 150f)
//                                    putFloat("btn_SYS_width", 80f)
//                                    putFloat("btn_SYS_height", 80f)
//                                }.apply()
//
//                                // THIS IS THE FIX: Just increment the trigger.
//                                // Compose sees the number change and instantly redraws the buttons.
//                                activity.layoutRefreshTrigger++
//                            }
//                        }
//                    )
//                }
//            }
//        }
//    }
//}
//
//@Composable
//fun SuperButton(
//    id: String,
//    label: String,
//    isActive: Boolean,
//    onToggle: (Boolean) -> Unit,
//    defaultX: Float,
//    defaultY: Float,
//    defaultWidth: Float = 80f,
//    defaultHeight: Float = 80f,
//    prefs: android.content.SharedPreferences,
//    activity: MainActivity
//) {
//    val isEditMode = activity.InEdit
//    val refreshTrigger = activity.layoutRefreshTrigger // Catch the trigger signal
//
//    // Pass BOTH variables as keys. If either one changes, the cache clears and reloads from disk!
//    var offsetX by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_x", defaultX)) }
//    var offsetY by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_y", defaultY)) }
//    var widthDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_width", defaultWidth)) }
//    var heightDp by remember(isEditMode, refreshTrigger) { mutableStateOf(prefs.getFloat("${id}_height", defaultHeight)) }
//
//    // Interaction Tracking Flags
//    var isDragging by remember { mutableStateOf(false) }
//    var isResizing by remember { mutableStateOf(false) }
//
//    Box(
//        modifier = Modifier
//            .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
//            .requiredSize(width = widthDp.dp, height = heightDp.dp)
//            .background(if (isActive) Color.Blue else Color.DarkGray, RoundedCornerShape(12.dp))
//            .pointerInput(isEditMode) {
//                if (isEditMode) {
//                    detectDragGestures(
//                        onDragStart = { isDragging = true },
//                        onDragEnd = {
//                            isDragging = false
//                            prefs.edit()
//                                .putFloat("${id}_x", offsetX)
//                                .putFloat("${id}_y", offsetY)
//                                .apply()
//                        },
//                        onDrag = { change, dragAmount ->
//                            change.consume()
//                            offsetX += dragAmount.x
//                            offsetY += dragAmount.y
//                        }
//                    )
//                } else {
//                    detectTapGestures(onPress = {
//                        onToggle(true)
//                        tryAwaitRelease()
//                        onToggle(false)
//                    })
//                }
//            },
//        contentAlignment = Alignment.Center
//    ) {
//        // Dynamic Text Telemetry Overlay
//        if (isEditMode && (isDragging || isResizing)) {
//            Column(horizontalAlignment = Alignment.CenterHorizontally) {
//                Text(
//                    text = "X:${offsetX.roundToInt()} Y:${offsetY.roundToInt()}",
//                    color = Color.Green,
//                    fontSize = 10.sp,
//                    lineHeight = 11.sp
//                )
//                Text(
//                    text = "W:${widthDp.roundToInt()} H:${heightDp.roundToInt()}",
//                    color = Color.Cyan,
//                    fontSize = 10.sp
//                )
//            }
//        } else {
//            val minDimension = minOf(widthDp, heightDp)
//            Text(label, color = Color.White, fontSize = (minDimension * 0.25f).sp)
//        }
//
//        // Custom Resize Handle
//        if (isEditMode) {
//            Box(
//                modifier = Modifier
//                    .size(24.dp)
//                    .align(Alignment.BottomEnd)
//                    .background(Color(0x88FFEB3B), RoundedCornerShape(topStart = 8.dp, bottomEnd = 12.dp))
//                    .pointerInput(Unit) {
//                        detectDragGestures(
//                            onDragStart = { isResizing = true },
//                            onDragEnd = {
//                                isResizing = false
//                                prefs.edit()
//                                    .putFloat("${id}_width", widthDp)
//                                    .putFloat("${id}_height", heightDp)
//                                    .apply()
//                            },
//                            onDrag = { change, dragAmount ->
//                                change.consume()
//                                widthDp = (widthDp + dragAmount.x).coerceAtLeast(50f)
//                                heightDp = (heightDp + dragAmount.y).coerceAtLeast(50f)
//                            }
//                        )
//                    }
//            ) {
//                Text("⤡", color = Color.Black, fontSize = 10.sp, modifier = Modifier.align(Alignment.Center))
//            }
//        }
//    }
//}

//;P

