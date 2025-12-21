from .auth import router as auth_router
from .owners import router as owners_router
from .vehicles import router as vehicles_router
from .violations import router as violations_router
from .detection import router as detection_router  # Add this

__all__ = ["auth_router", "owners_router", "vehicles_router", 
           "violations_router", "detection_router"]  # Update this