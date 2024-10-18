from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class ImageSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and "image" in request.url.path:
            form = await request.form()
            upload_image = form.get("upload_image")
            if upload_image is not None:
                contents = await upload_image.read()
                if len(contents) > 20 * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail="Image size must be less than 20MB"
                    )
        response = await call_next(request)
        return response
