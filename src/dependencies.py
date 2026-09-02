from src.core.di import include_core_dependencies
from src.domains.pauses.di import include_pause_dependencies
from src.domains.shifts.di import include_shift_dependencies


include_core_dependencies()
include_shift_dependencies()
include_pause_dependencies()
