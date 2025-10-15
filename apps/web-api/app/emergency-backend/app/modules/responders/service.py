from app.security.password import hash_password
from .repo import create_user

async def admin_create_user(name, email, role, password):
    ph = hash_password(password)
    return await create_user(name, email, role, ph)
