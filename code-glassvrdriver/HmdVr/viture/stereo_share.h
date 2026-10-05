#pragma once
#include <windows.h>
#include <atomic>
#include <cstdint>
#include <cstring>

struct StereoShmHeader {
    uint32_t magic;
    uint32_t _pad0;
    std::atomic<uint64_t> seq;
    uint32_t width;
    uint32_t height;
    double   timestamp;
};

class StereoShare {
public:
    static constexpr uint32_t MAGIC = 0x56535452;
    static constexpr size_t MAX_W = 1280;
    static constexpr size_t MAX_H = 800;
    static constexpr size_t MAX_FRAME = MAX_W * MAX_H;
    static constexpr size_t TOTAL_SIZE = sizeof(StereoShmHeader) + MAX_FRAME * 2;

    bool init(const wchar_t* name = L"GlassVRStereoCam") {
        if (m_view) {
            OutputDebugStringA("[StereoShare] init() called twice, ignoring\n");
            return true;
        }

        SetLastError(0);
        m_map = CreateFileMappingW(INVALID_HANDLE_VALUE, nullptr, PAGE_READWRITE,
            0, (DWORD)TOTAL_SIZE, name);
        DWORD create_err = GetLastError();

        if (!m_map) {
            char buf[128];
            sprintf_s(buf, "[StereoShare] CreateFileMappingW FAILED, err=%lu\n", create_err);
            OutputDebugStringA(buf);
            return false;
        }

        if (create_err == ERROR_ALREADY_EXISTS) {
            OutputDebugStringA("[StereoShare] WARNING: mapping already existed "
                "(reader started before writer, or protection mismatch) - "
                "start the C++ app BEFORE the Python viewer\n");
        }

        m_view = (uint8_t*)MapViewOfFile(m_map, FILE_MAP_ALL_ACCESS, 0, 0, TOTAL_SIZE);
        if (!m_view) {
            char buf[128];
            sprintf_s(buf, "[StereoShare] MapViewOfFile FAILED, err=%lu (likely protection "
                "mismatch with a pre-existing read-only section)\n", GetLastError());
            OutputDebugStringA(buf);
            CloseHandle(m_map); m_map = nullptr;
            return false;
        }

        m_hdr = reinterpret_cast<StereoShmHeader*>(m_view);
        m_hdr->magic = MAGIC;
        m_hdr->seq = 0;
        m_hdr->width = 0;
        m_hdr->height = 0;
        m_left = m_view + sizeof(StereoShmHeader);
        m_right = m_left + MAX_FRAME;

        char buf[160];
        sprintf_s(buf, "[StereoShare] init OK, map=%p view=%p total_size=%zu\n",
            (void*)m_map, (void*)m_view, TOTAL_SIZE);
        OutputDebugStringA(buf);
        return true;
    }

    void write_frame(const char* left0, const char* right0, double ts, int w, int h) {
        if (!m_view) {
            static int warn_count = 0;
            if (warn_count++ < 3)
                OutputDebugStringA("[StereoShare] write_frame() called but m_view is null "
                    "(init() never succeeded)\n");
            return;
        }
        size_t frame_bytes = (size_t)w * (size_t)h;
        if (frame_bytes == 0 || frame_bytes > MAX_FRAME) {
            char buf[128];
            sprintf_s(buf, "[StereoShare] write_frame() rejected frame %dx%d (max %zux%zu)\n",
                w, h, MAX_W, MAX_H);
            OutputDebugStringA(buf);
            return;
        }

        uint64_t s = m_hdr->seq.load(std::memory_order_relaxed);
        m_hdr->seq.store(s + 1, std::memory_order_release);

        m_hdr->width = w;
        m_hdr->height = h;
        m_hdr->timestamp = ts;
        memcpy(m_left, left0, frame_bytes);
        memcpy(m_right, right0, frame_bytes);

        m_hdr->seq.store(s + 2, std::memory_order_release);

        static uint64_t frame_count = 0;
        if (++frame_count % 75 == 0) {
            char buf[128];
            sprintf_s(buf, "[StereoShare] wrote frame #%llu (%dx%d) ts=%.3f\n",
                (unsigned long long)frame_count, w, h, ts);
            OutputDebugStringA(buf);
        }
    }

    ~StereoShare() {
        if (m_view) UnmapViewOfFile(m_view);
        if (m_map)  CloseHandle(m_map);
    }

private:
    HANDLE m_map = nullptr;
    uint8_t* m_view = nullptr;
    StereoShmHeader* m_hdr = nullptr;
    uint8_t* m_left = nullptr;
    uint8_t* m_right = nullptr;
};