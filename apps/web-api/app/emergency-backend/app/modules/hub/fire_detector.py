# Stub for fire detection. Replace with your ML inference later.
# Keep the signature stable so priority logic doesn't change.
from typing import Optional

async def fire_present_from_image(image_url: Optional[str]) -> bool:
    # Simple rule: if image_url contains "fire" we return True (useful in demos).
    if not image_url:
        return False
    return "fire" in image_url.lower()
