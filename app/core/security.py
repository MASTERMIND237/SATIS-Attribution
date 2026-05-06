import os

from fastapi import Header, HTTPException, status


ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "Master_mind237")


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_API_KEY n'est pas configurée sur le serveur.",
        )

    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès admin refusé.",
        )
