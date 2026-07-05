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

    bool is_carina() const;

    void get_imu_data(float euler_out[3], float quat_out[4], float gyro_out[3]);

    bool get_6dof_pose(float quat_out[4], float pos_out[3], bool* stable_out = nullptr);

    void recenter();

    void recenter_6dof();

    void reset_origin_carina();

    void recenter_3dof();

    bool m_3dof_recentered = false;
    float m_3dof_inv_quat[4] = { 1.f, 0.f, 0.f, 0.f };
    float m_raw_quat[4] = { 1.f, 0.f, 0.f, 0.f };
    float m_3dof_quat[4] = { 1.f, 0.f, 0.f, 0.f };
    float m_3dof_ref_inv_quat[4] = { 1.f, 0.f, 0.f, 0.f };

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

    std::mutex         m_6dof_mutex;
    float              m_carina_quat[4] = { 0, 0, 0, 1 };
    float              m_carina_pos[3] = { 0, 0, 0 };
    int                m_carina_status = 1;
    bool               m_carina_fresh = false;

    float              m_ref_inv_quat[4] = { 0, 0, 0, 1 };
    float              m_ref_pos[3] = { 0, 0, 0 };
    bool               m_6dof_recentered = false;
};

#endif