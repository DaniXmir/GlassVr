package com.example.GlassVR

import android.media.MediaCodec
import android.media.MediaFormat
import android.view.Surface
import android.view.SurfaceHolder
import android.view.SurfaceView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.isActive
import kotlinx.coroutines.withContext
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.SocketTimeoutException

//super sloppy, very slow, plz ignore
@Composable
fun HeadsetVideoView(
    videoPort: Int,
    modifier: Modifier = Modifier
) {
    // Holds the Surface once SurfaceView is ready. The decode coroutine is
    // keyed on this so it restarts automatically if the surface is recreated.
    var activeSurface by remember { mutableStateOf<Surface?>(null) }

    Box(modifier = modifier.background(Color.Black)) {
        AndroidView(
            modifier = Modifier.fillMaxSize(),
            factory = { ctx ->
                SurfaceView(ctx).apply {
                    holder.addCallback(object : SurfaceHolder.Callback {
                        override fun surfaceCreated(h: SurfaceHolder) {
                            activeSurface = h.surface
                        }
                        override fun surfaceChanged(h: SurfaceHolder, fmt: Int, w: Int, h2: Int) {}
                        override fun surfaceDestroyed(h: SurfaceHolder) {
                            activeSurface = null
                        }
                    })
                }
            }
        )
    }

    // Start/restart the decode loop whenever the surface or port changes.
    // LaunchedEffect cancels the previous coroutine automatically on recompose.
    val surface = activeSurface
    if (surface != null) {
        LaunchedEffect(surface, videoPort) {
            withContext(Dispatchers.IO) {
                decodeH264UdpToSurface(surface, videoPort) { isActive }
            }
        }
    }
}

/**
 * Blocking decode loop. Runs on an IO thread until [isRunning] returns false
 * (checked every 100 ms via socket timeout) or an unrecoverable error occurs.
 *
 * Input packets are fed directly to MediaCodec's byte-stream input queue.
 * Decoded frames are released to [surface] for immediate display.
 * Dropped UDP packets cause decode errors that MediaCodec recovers from on
 * the next keyframe.
 */
fun decodeH264UdpToSurface(
    surface: Surface,
    port: Int,
    isRunning: () -> Boolean
) {
    var codec: MediaCodec? = null
    var socket: DatagramSocket? = null

    try {
        socket = DatagramSocket(port).apply {
            receiveBufferSize = 8 * 1024 * 1024
            soTimeout = 100 // ms — lets us check isRunning() periodically
        }

        codec = MediaCodec.createDecoderByType("video/avc")
        val format = MediaFormat.createVideoFormat("video/avc", 1920, 1080).apply {
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
                setInteger(MediaFormat.KEY_LOW_LATENCY, 1)
            }
        }
        codec.configure(format, surface, null, 0)
        codec.start()

        val recvBuf = ByteArray(65_536)
        val packet = DatagramPacket(recvBuf, recvBuf.size)
        val outInfo = MediaCodec.BufferInfo()

        // Buffer to accumulate fragments into complete NAL Units
        val streamBuffer = ByteArray(2 * 1024 * 1024) // 2MB
        var streamLen = 0

        // Helper to drain frames to the surface
        fun drainOutputFrames() {
            var outIdx = codec!!.dequeueOutputBuffer(outInfo, 0)
            while (outIdx >= 0) {
                codec!!.releaseOutputBuffer(outIdx, true)
                outIdx = codec!!.dequeueOutputBuffer(outInfo, 0)
            }
        }

        while (isRunning()) {
            // --- 1. Receive UDP payload ---
            try {
                socket.receive(packet)
            } catch (e: SocketTimeoutException) {
                drainOutputFrames() // Poll output even if we timeout waiting
                continue
            }
            val len = packet.length
            if (len == 0) continue

            // --- 2. Append to reassembly buffer ---
            if (streamLen + len > streamBuffer.size) {
                // Safety valve: buffer overflowed without finding a NAL unit.
                // Means the stream is severely corrupted. Reset to recover.
                streamLen = 0
            }
            System.arraycopy(recvBuf, 0, streamBuffer, streamLen, len)
            streamLen += len

            // --- 3. Scan for Annex-B NAL Unit Start Codes ---
            var i = 0
            var lastStartCodeIdx = -1

            while (i <= streamLen - 3) {
                // Match 0x00 0x00 0x01
                if (streamBuffer[i] == 0.toByte() &&
                    streamBuffer[i+1] == 0.toByte() &&
                    streamBuffer[i+2] == 1.toByte()) {

                    // Include the preceding zero if the start code is 0x00 0x00 0x00 0x01
                    val startIndex = if (i > 0 && streamBuffer[i-1] == 0.toByte()) i - 1 else i

                    if (lastStartCodeIdx != -1) {
                        // We found a complete NAL unit bounded by two start codes
                        val naluLen = startIndex - lastStartCodeIdx

                        var inputIdx = codec.dequeueInputBuffer(0)
                        var retries = 0
                        // If no input slots, drain output to free up slots and try again
                        while (inputIdx < 0 && retries < 50 && isRunning()) {
                            drainOutputFrames()
                            inputIdx = codec.dequeueInputBuffer(1000L) // Wait 1ms
                            retries++
                        }

                        if (inputIdx >= 0) {
                            val buf = codec.getInputBuffer(inputIdx)
                            if (buf != null) {
                                buf.clear()
                                buf.put(streamBuffer, lastStartCodeIdx, naluLen)
                                codec.queueInputBuffer(
                                    inputIdx, 0, naluLen,
                                    System.nanoTime() / 1_000L,
                                    0
                                )
                            }
                        }
                    }
                    lastStartCodeIdx = startIndex
                    i += 3 // Skip past the checked 00 00 01
                } else {
                    i++
                }
            }

            // --- 4. Keep the trailing incomplete NAL unit for the next packet ---
            if (lastStartCodeIdx != -1) {
                val remaining = streamLen - lastStartCodeIdx
                System.arraycopy(streamBuffer, lastStartCodeIdx, streamBuffer, 0, remaining)
                streamLen = remaining
            } else if (streamLen > 1024 * 1024) {
                streamLen = 0 // Drop bad data if we haven't found a start code in 1MB
            }

            // --- 5. Output Decoded Frames ---
            drainOutputFrames()
        }

    } catch (e: Exception) {
        e.printStackTrace()
    } finally {
        try { codec?.stop(); codec?.release() } catch (_: Exception) {}
        try { socket?.close() } catch (_: Exception) {}
    }
}