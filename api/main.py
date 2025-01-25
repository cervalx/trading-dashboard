from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import StreamingResponse
from starlette.types import ASGIApp
import uvicorn
from modules.telegram_bot import bot_alerts
from modules.tradingedge_scraper import scraper
from fastapi_utils.tasks import repeat_every


class StreamlitAppMiddleware(BaseHTTPMiddleware):
    """Middleware to serve Streamlit app."""

    def __init__(self, app: ASGIApp, streamlit_app_path: str) -> None:
        super().__init__(app)
        self.streamlit_app_path = streamlit_app_path

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StreamingResponse:
        if str(request.url.path) == "/" or str(request.url.path).startswith("/static"):
            # Modified condition to serve Streamlit on root path or static files
            return await self.handle_streamlit_request(request)
        else:
            return await call_next(request)

    async def handle_streamlit_request(self, request: Request) -> StreamingResponse:
        # Prepare a modified scope that includes the root_path
        modified_scope = request.scope.copy()
        modified_scope["root_path"] = self.streamlit_app_path
        modified_scope["path"] = "/"

        # Create a new Request with the modified scope
        modified_request = Request(modified_scope, receive=request.receive)

        # Fetch response from Streamlit
        async with self.app.router.lifespan_context(self.app) as state:
            response = await self.app(
                modified_request.scope, modified_request.receive, self.send_wrapper()
            )
        return response

    async def send_wrapper(self):
        """Wrapper for sending responses."""

        async def mock_send(message):
            pass

        return mock_send


app = FastAPI()


@repeat_every(seconds=60 * 5)
async def send_telegram_alerts():
    await bot_alerts.main()


@repeat_every(seconds=60 * 60)
def scrape_posts():
    scraper.main()


# API endpoint
@app.get("/api/data")
async def get_data():
    return {"message": "Data from FastAPI"}


# Redirect /api to the /api/ documentation
@app.get("/api")
async def redirect_api_docs():
    return RedirectResponse(url="/api/docs")


# Mount the Streamlit app
streamlit_base_url_path = "/"

app.add_middleware(StreamlitAppMiddleware, streamlit_app_path=streamlit_base_url_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
