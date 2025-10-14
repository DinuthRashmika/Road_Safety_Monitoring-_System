from datetime import datetime
from typing import Optional

def user_doc(
    *,
    fullName: str,
    email: str,
    phone: str,
    address: str,
    nic: str,
    passwordHash: str,
    imageUrl: Optional[str] = None,
):
    now = datetime.utcnow()
    return {
        "fullName": fullName,
        "email": email.lower(),
        "phone": phone,
        "address": address,
        "nic": nic.upper(),
        "passwordHash": passwordHash,
        "role": "owner",
        "imageUrl": imageUrl,
        "createdAt": now,
        "updatedAt": now,
    }
