#ifndef VITURE_H
#define VITURE_H

#include <atomic>
#include <chrono>
#include <mutex>
#include <thread>

class Viture {
public:
    Viture();
    ~Viture();

    bool is_connected() const;
    void get_imu_data(float euler_out[3], float quat_out[4], float gyro_out[3]);
    void recenter();

private:
    void monitor_thread_func();
    void fusion_thread_func();

    void reset_imu_data();

    std::atomic<bool>  m_running;
    std::atomic<bool>  m_connected;
    std::thread        m_monitor_thread;
    std::thread        m_fusion_thread;
    void* m_device_handle;
    int                m_device_type;

    alignas(16) float  m_quat_atomic[4];
    alignas(16) float  m_gyro_atomic[3];
    alignas(16) float  m_accel_atomic[3];
    alignas(16) float  m_mag_atomic[3];
    std::atomic<bool>  m_raw_data_fresh{ false };

    std::mutex         m_imu_mutex;
    alignas(16) float  m_fused_quat[4];
    alignas(16) float  m_base_quat[4];
    alignas(16) float  m_euler[3];

    std::chrono::steady_clock::time_point m_last_imu_time;

    static Viture* s_instance;
    static void static_imu_pose_callback(float* data, uint64_t ts);
    static void static_imu_raw_callback(float* data, uint64_t ts, uint64_t vsync);

    alignas(16) float m_euler_atomic[3];

    std::atomic<bool> m_first_sample{ true };
};

#endif