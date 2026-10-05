#ifndef GLASSVR_DRIVERHOOKS_H
#define GLASSVR_DRIVERHOOKS_H

#include <openvr_driver.h>
#include <string>
#include <cstdint>

namespace glassvr {
	namespace hooks {

		bool Install(vr::IVRDriverContext* pDriverContext);

		void Remove();

		void SetSerialBlocked(const std::string& serial, bool blocked);

		void SetSerialHidden(const std::string& serial, bool hidden);

		void SetSerialModelVisible(const std::string& serial, bool visible);

		void SetSerialPositionOffset(const std::string& serial, double x, double y, double z);
		void ClearSerialPositionOffset(const std::string& serial);

		void SetPoseSource(const std::string& targetSerial, const std::string& sourceSerial);
		void ClearPoseSource(const std::string& targetSerial);

		void SetSerialRole(const std::string& serial, vr::ETrackedControllerRole role);
		void ClearSerialRole(const std::string& serial);

		void ClearAllRules();

		void TickPropertyRules();

		std::string SerialForDeviceIndex(uint32_t unWhichDevice);
		uint32_t    DeviceIndexForSerial(const std::string& serial);

	}
}

#endif