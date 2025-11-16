from typing import Optional

async def fire_present_from_image(image_url: Optional[str]) -> bool:
    
    if not image_url:
        return False
    return "fire" in image_url.lower()
