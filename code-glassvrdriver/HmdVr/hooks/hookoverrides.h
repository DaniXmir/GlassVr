#ifndef GLASSVR_HOOKOVERRIDES_H
#define GLASSVR_HOOKOVERRIDES_H

#include <string>

namespace glassvr {
	namespace hooks {
		namespace overrides {

			void Start(int pollIntervalMs = 250);

			void Stop();

			void PollOnce();

			extern const char* kOverridesKey;

		}
	}
}

#endif