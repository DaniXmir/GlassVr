#define _CRT_SECURE_NO_WARNINGS

#include "viture.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <vector>

#if defined(_WIN32)
#  include <windows.h>
#  include <cfgmgr32.h>
#  include <setupapi.h>
#  pragma comment(lib, "setupapi.lib")
#elif defined(__APPLE__)
#  include <CoreFoundation/CoreFoundation.h>
#  include <IOKit/IOKitLib.h>
#  include <IOKit/usb/IOUSBLib.h>
#else
#  include <dirent.h>
#endif

#include "hidapi.h"
#include "viture_device.h"
#include "viture_device_carina.h"
#include "viture_glasses_provider.h"
#include "viture_protocol_public.h"

Viture* Viture::s_instance = nullptr;

namespace {

    static void QuatMultiply(const float q1[4], const float q2[4], float out[4]) {
        float x = q1[3] * q2[0] + q1[0] * q2[3] + q1[1] * q2[2] - q1[2] * q2[1];
        float y = q1[3] * q2[1] - q1[0] * q2[2] + q1[1] * q2[3] + q1[2] * q2[0];
        float z = q1[3] * q2[2] + q1[0] * q2[1] - q1[1] * q2[0] + q1[2] * q2[3];
        float w = -q1[0] * q2[0] - q1[1] * q2[1] - q1[2] * q2[2] + q1[3] * q2[3];
        out[0] = x; out[1] = y; out[2] = z; out[3] = w;
    }

    static void QuatNormalize(float q[4]) {
        float n = std::sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
        if (n < 1e-6f) { q[0] = 0; q[1] = 0; q[2] = 0; q[3] = 1; return; }
        q[0] /= n; q[1] /= n; q[2] /= n; q[3] /= n;
    }

    static void QuatConjugate(const float q[4], float out[4]) {
        out[0] = -q[0]; out[1] = -q[1]; out[2] = -q[2]; out[3] = q[3];
    }

    static bool QuatFromAccelMag(const float accel[3], const float mag[3], float q_out[4]) {
        float ax = accel[0], ay = accel[1], az = accel[2];
        float an = std::sqrt(ax * ax + ay * ay + az * az);
        if (an < 0.01f) return false;
        ax /= an; ay /= an; az /= an;

        float pitch = std::asin(-ax);
        float roll = std::atan2(ay, az);
        float cp = std::cos(pitch), sp = std::sin(pitch);
        float cr = std::cos(roll), sr = std::sin(roll);

        float mx = mag[0], my = mag[1], mz = mag[2];
        float mn = std::sqrt(mx * mx + my * my + mz * mz);
        if (mn < 0.01f) return false;
        mx /= mn; my /= mn; mz /= mn;

        float hx = mx * cp + my * sr * sp + mz * cr * sp;
        float hy = my * cr - mz * sr;
        float yaw = std::atan2(-hy, hx);

        float cy = std::cos(yaw * 0.5f), sy = std::sin(yaw * 0.5f);
        float cP = std::cos(pitch * 0.5f), sP = std::sin(pitch * 0.5f);
        float cR = std::cos(roll * 0.5f), sR = std::sin(roll * 0.5f);

        q_out[3] = cy * cP * cR + sy * sP * sR;  // w
        q_out[0] = cy * cP * sR - sy * sP * cR;  // x
        q_out[1] = sy * cP * sR + cy * sP * cR;  // y
        q_out[2] = sy * cP * cR - cy * sP * sR;  // z
        QuatNormalize(q_out);
        return true;
    }

    static void QuatSlerp(const float q1[4], const float q2[4], float t, float out[4]) {
        float dot = q1[0] * q2[0] + q1[1] * q2[1] + q1[2] * q2[2] + q1[3] * q2[3];
        float q2s[4] = { q2[0],q2[1],q2[2],q2[3] };
        if (dot < 0.f) {
            dot = -dot;
            q2s[0] = -q2s[0]; q2s[1] = -q2s[1]; q2s[2] = -q2s[2]; q2s[3] = -q2s[3];
        }
        if (dot > 0.9995f) {
            for (int i = 0;i < 4;i++) out[i] = q1[i] + t * (q2s[i] - q1[i]);
            QuatNormalize(out);
            return;
        }
        float theta0 = std::acos(dot);
        float theta = theta0 * t;
        float s1 = std::cos(theta) - dot * std::sin(theta) / std::sin(theta0);
        float s2 = std::sin(theta) / std::sin(theta0);
        for (int i = 0;i < 4;i++) out[i] = s1 * q1[i] + s2 * q2s[i];
        QuatNormalize(out);
    }

#if defined(_WIN32)
#elif defined(__APPLE__)
    static bool getUSBProperty(io_service_t service, const char* key, uint16_t* outValue) {
        CFStringRef keyStr = CFStringCreateWithCString(kCFAllocatorDefault, key, kCFStringEncodingUTF8);
        CFTypeRef   prop = IORegistryEntryCreateCFProperty(service, keyStr, kCFAllocatorDefault, 0);
        CFRelease(keyStr);
        if (!prop) return false;
        bool ok = (CFNumberGetTypeID() == CFGetTypeID(prop)) &&
            CFNumberGetValue((CFNumberRef)prop, kCFNumberShortType, outValue);
        CFRelease(prop);
        return ok;
    }
#else
    static bool read_int_from_file(const char* path, int* out_value) {
        if (!path || !out_value) return false;
        FILE* f = std::fopen(path, "r");
        if (!f) return false;
        char buf[64]{};
        bool ok = (std::fgets(buf, sizeof(buf), f) != nullptr);
        std::fclose(f);
        if (!ok) return false;
        size_t len = std::strlen(buf);
        while (len > 0 && (buf[len - 1] == '\n' || buf[len - 1] == '\r' || buf[len - 1] == ' ' || buf[len - 1] == '\t'))
            buf[--len] = '\0';
        char* ep = nullptr;
        long v = std::strtol(buf, &ep, 16);
        if (ep == buf) return false;
        *out_value = static_cast<int>(v);
        return true;
    }
#endif

    static bool autodetect_viture_usb_fallback(std::vector<int>& out_pids) {
#if defined(_WIN32)
        HDEVINFO devInfo = SetupDiGetClassDevsA(NULL, "USB", NULL, DIGCF_PRESENT | DIGCF_ALLCLASSES);
        if (devInfo == INVALID_HANDLE_VALUE) return false;
        SP_DEVINFO_DATA did; did.cbSize = sizeof(did);
        for (DWORD i = 0; SetupDiEnumDeviceInfo(devInfo, i, &did); ++i) {
            DWORD rt = 0; BYTE buf[4096] = { 0 };
            if (SetupDiGetDeviceRegistryPropertyA(devInfo, &did, SPDRP_HARDWAREID, &rt, buf, sizeof(buf), NULL)) {
                for (const char* p = (const char*)buf; *p; p += std::strlen(p) + 1) {
                    const char* vp = strstr(p, "VID_"), * pp = strstr(p, "PID_");
                    if (vp && pp) {
                        unsigned vid = 0, pid = 0;
                        if (sscanf(vp + 4, "%4x", &vid) == 1 && sscanf(pp + 4, "%4x", &pid) == 1 && vid == 0x35CA)
                            if (std::find(out_pids.begin(), out_pids.end(), (int)pid) == out_pids.end())
                                out_pids.push_back((int)pid);
                    }
                }
            }
        }
        SetupDiDestroyDeviceInfoList(devInfo);
        return !out_pids.empty();
#elif defined(__APPLE__)
        CFMutableDictionaryRef md = IOServiceMatching(kIOUSBDeviceClassName);
        if (!md) return false;
        io_iterator_t it = 0;
        if (IOServiceGetMatchingServices(0, md, &it) != KERN_SUCCESS || !it) return false;
        io_service_t svc;
        while ((svc = IOIteratorNext(it))) {
            uint16_t vid = 0, pid = 0;
            if (getUSBProperty(svc, kUSBVendorID, &vid) && vid == 0x35CA && getUSBProperty(svc, kUSBProductID, &pid))
                if (std::find(out_pids.begin(), out_pids.end(), (int)pid) == out_pids.end())
                    out_pids.push_back((int)pid);
            IOObjectRelease(svc);
        }
        IOObjectRelease(it);
        return !out_pids.empty();
#else
        DIR* dir = opendir("/sys/bus/usb/devices"); if (!dir) return false;
        struct dirent* ent;
        while ((ent = readdir(dir)) != nullptr) {
            if (ent->d_name[0] == '.' || std::strchr(ent->d_name, ':')) continue;
            char idV[600], idP[600];
            std::snprintf(idV, sizeof(idV), "/sys/bus/usb/devices/%s/idVendor", ent->d_name);
            std::snprintf(idP, sizeof(idP), "/sys/bus/usb/devices/%s/idProduct", ent->d_name);
            int vid = 0, pid = 0;
            if (read_int_from_file(idV, &vid) && read_int_from_file(idP, &pid) && vid == 0x35CA)
                if (std::find(out_pids.begin(), out_pids.end(), pid) == out_pids.end())
                    out_pids.push_back(pid);
        }
        closedir(dir);
        return !out_pids.empty();
#endif
    }

    static bool autodetect_viture_usb(std::vector<int>& out_pids) {
        if (hid_init() != 0) return false;
        hid_device_info* devs = hid_enumerate(0, 0);
        if (!devs) { hid_exit(); return false; }
        for (hid_device_info* c = devs; c; c = c->next)
            if ((int)c->vendor_id == 0x35CA) {
                int pid = (int)c->product_id;
                if (std::find(out_pids.begin(), out_pids.end(), pid) == out_pids.end())
                    out_pids.push_back(pid);
            }
        hid_free_enumeration(devs);
        hid_exit();
        return !out_pids.empty();
    }

}

Viture::Viture()
    : m_running(true), m_connected(false),
    m_device_handle(nullptr), m_device_type(0)
{
    s_instance = this;

    m_quat_atomic[0] = 0; m_quat_atomic[1] = 0; m_quat_atomic[2] = 0; m_quat_atomic[3] = 1;
    m_gyro_atomic[0] = 0; m_gyro_atomic[1] = 0; m_gyro_atomic[2] = 0;
    m_accel_atomic[0] = 0; m_accel_atomic[1] = 0; m_accel_atomic[2] = 1;
    m_mag_atomic[0] = 1;  m_mag_atomic[1] = 0;  m_mag_atomic[2] = 0;

    reset_imu_data();
    m_last_imu_time = std::chrono::steady_clock::now();

    m_fusion_thread = std::thread(&Viture::fusion_thread_func, this);
    m_monitor_thread = std::thread(&Viture::monitor_thread_func, this);
}

Viture::~Viture() {
    m_running = false;
    if (m_fusion_thread.joinable())  m_fusion_thread.join();
    if (m_monitor_thread.joinable()) m_monitor_thread.join();

    if (m_device_handle) {
        if (m_device_type == XR_DEVICE_TYPE_VITURE_GEN1 || m_device_type == XR_DEVICE_TYPE_VITURE_GEN2)
            xr_device_provider_close_imu(m_device_handle, VITURE_IMU_MODE_POSE);
        xr_device_provider_stop(m_device_handle);
        xr_device_provider_shutdown(m_device_handle);
        xr_device_provider_destroy(m_device_handle);
    }
    s_instance = nullptr;
}

bool Viture::is_connected() const { return m_connected; }

void Viture::get_imu_data(float euler_out[3], float quat_out[4], float gyro_out[3]) {
    euler_out[0] = m_euler[0];
    euler_out[1] = m_euler[1];
    euler_out[2] = m_euler[2];
    gyro_out[0] = m_gyro_atomic[0];
    gyro_out[1] = m_gyro_atomic[1];
    gyro_out[2] = m_gyro_atomic[2];

    std::lock_guard<std::mutex> lk(m_imu_mutex);
    quat_out[0] = m_fused_quat[0];
    quat_out[1] = m_fused_quat[1];
    quat_out[2] = m_fused_quat[2];
    quat_out[3] = m_fused_quat[3];
}

void Viture::recenter() {
    std::lock_guard<std::mutex> lk(m_imu_mutex);

    float w = m_fused_quat[3];
    float y = m_fused_quat[1];

    float yaw_len = std::sqrt(w * w + y * y);
    if (yaw_len < 1e-6f) return;

    m_base_quat[0] = 0.f;
    m_base_quat[1] = y / yaw_len;
    m_base_quat[2] = 0.f;
    m_base_quat[3] = w / yaw_len;
}

void Viture::static_imu_pose_callback(float* data, uint64_t) {
    Viture* v = s_instance;
    if (!v) return;

    v->m_euler[0] = data[0];
    v->m_euler[1] = data[1];
    v->m_euler[2] = data[2];

    v->m_euler_atomic[0] = data[0];
    v->m_euler_atomic[1] = data[1];
    v->m_euler_atomic[2] = data[2];

    v->m_quat_atomic[0] = data[3];
    v->m_quat_atomic[1] = data[4];
    v->m_quat_atomic[2] = data[5];
    v->m_quat_atomic[3] = data[6];

    v->m_last_imu_time = std::chrono::steady_clock::now();
    v->m_raw_data_fresh.store(true, std::memory_order_release);
}

void Viture::static_imu_raw_callback(float* data, uint64_t, uint64_t) {
    Viture* v = s_instance;
    if (!v) return;

    const float d2r = 3.14159265f / 180.f;
    v->m_gyro_atomic[0] = data[0] * d2r;
    v->m_gyro_atomic[1] = data[1] * d2r;
    v->m_gyro_atomic[2] = data[2] * d2r;

    v->m_accel_atomic[0] = data[3];
    v->m_accel_atomic[1] = data[4];
    v->m_accel_atomic[2] = data[5];

    v->m_mag_atomic[0] = data[6];
    v->m_mag_atomic[1] = data[7];
    v->m_mag_atomic[2] = data[8];
}

void Viture::fusion_thread_func() {
#if defined(_WIN32)
    SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_BELOW_NORMAL);
#endif

    float prev_fused[4] = { 0,0,0,1 };

    while (m_running) {
        if (!m_raw_data_fresh.exchange(false, std::memory_order_acquire)) {
            std::this_thread::sleep_for(std::chrono::microseconds(200));
            continue;
        }

        float fused[4];
        fused[0] = m_quat_atomic[0];
        fused[1] = m_quat_atomic[1];
        fused[2] = m_quat_atomic[2];
        fused[3] = m_quat_atomic[3];
        QuatNormalize(fused);

        float dot = fused[0] * prev_fused[0] + fused[1] * prev_fused[1]
            + fused[2] * prev_fused[2] + fused[3] * prev_fused[3];
        if (dot < 0.f) {
            fused[0] = -fused[0]; fused[1] = -fused[1];
            fused[2] = -fused[2]; fused[3] = -fused[3];
        }
        prev_fused[0] = fused[0]; prev_fused[1] = fused[1];
        prev_fused[2] = fused[2]; prev_fused[3] = fused[3];

        {
            std::lock_guard<std::mutex> lk(m_imu_mutex);
            m_fused_quat[0] = fused[0];
            m_fused_quat[1] = fused[1];
            m_fused_quat[2] = fused[2];
            m_fused_quat[3] = fused[3];
        }
    }
}

void Viture::monitor_thread_func() {
    while (m_running) {
        if (!m_connected) {
            std::vector<int> pids;
            autodetect_viture_usb(pids);
            if (pids.empty()) autodetect_viture_usb_fallback(pids);

            if (!pids.empty()) {
                int pid = pids[0];
                m_device_handle = xr_device_provider_create(pid);
                if (m_device_handle) {
                    m_device_type = xr_device_provider_get_device_type(m_device_handle);

                    if (m_device_type == XR_DEVICE_TYPE_VITURE_GEN1 ||
                        m_device_type == XR_DEVICE_TYPE_VITURE_GEN2) {
                        xr_device_provider_register_imu_pose_callback(
                            m_device_handle, Viture::static_imu_pose_callback);
                        xr_device_provider_register_imu_raw_callback(
                            m_device_handle, Viture::static_imu_raw_callback);
                    }

                    if (xr_device_provider_initialize(m_device_handle) == 0 &&
                        xr_device_provider_start(m_device_handle) == 0) {

                        if (m_device_type == XR_DEVICE_TYPE_VITURE_GEN1 ||
                            m_device_type == XR_DEVICE_TYPE_VITURE_GEN2)
                            xr_device_provider_open_imu(m_device_handle,
                                VITURE_IMU_MODE_POSE, VITURE_IMU_FREQUENCY_HIGH);

                        m_last_imu_time = std::chrono::steady_clock::now();
                        m_connected = true;
                    }
                    else {
                        xr_device_provider_destroy(m_device_handle);
                        m_device_handle = nullptr;
                    }
                }
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(500));

        }
        else {
            if (m_device_type == XR_DEVICE_TYPE_VITURE_CARINA) {
                float pose[7] = { 0 }; int pose_status = 0;
                if (xr_device_provider_get_gl_pose_carina(m_device_handle, pose, 0.0, &pose_status) == 0) {
                    m_quat_atomic[0] = pose[0]; m_quat_atomic[1] = pose[1];
                    m_quat_atomic[2] = pose[2]; m_quat_atomic[3] = pose[3];
                    m_raw_data_fresh.store(true, std::memory_order_release);
                    m_last_imu_time = std::chrono::steady_clock::now();
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(5));

            }
            else {
                auto elapsed = std::chrono::steady_clock::now() - m_last_imu_time;
                if (elapsed > std::chrono::seconds(3)) {
                    m_connected = false;
                    reset_imu_data();
                    if (m_device_handle) {
                        xr_device_provider_stop(m_device_handle);
                        xr_device_provider_shutdown(m_device_handle);
                        xr_device_provider_destroy(m_device_handle);
                        m_device_handle = nullptr;
                    }
                }

                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
        }
    }
}

void Viture::reset_imu_data() {
    std::lock_guard<std::mutex> lk(m_imu_mutex);
    memset(m_euler, 0, sizeof(m_euler));
    m_fused_quat[0] = 0; m_fused_quat[1] = 0; m_fused_quat[2] = 0; m_fused_quat[3] = 1;
    m_base_quat[0] = 0; m_base_quat[1] = 0; m_base_quat[2] = 0; m_base_quat[3] = 1;
    m_first_sample.store(true);
}