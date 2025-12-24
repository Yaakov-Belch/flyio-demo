from pathlib import Path
from fastmcp import FastMCP
from code_insight.add_numbers import add

mcp = FastMCP("Demo")

@mcp.tool
def mirror_tool(text: str) -> str:
    """Mirror a text"""
    return text[::-1]

mcp.tool(add)

@mcp.prompt
def hello() -> str:
    """A simple greeting prompt"""
    return "Hello world!"

@mcp.prompt
def hallo() -> str:
    """Eine einfache Begrüßungsaufforderung"""
    return "Hallo Welt!"

from starlette.requests import Request
from starlette.responses import PlainTextResponse, FileResponse, HTMLResponse, RedirectResponse

@mcp.custom_route("/info", methods=["GET"])
async def show_info(request: Request) -> PlainTextResponse:
    return PlainTextResponse("Health Ok!")


# Configure static files directory
STATIC_DIR = Path(__file__).parent / "static"

@mcp.custom_route("/static/{filepath:path}", methods=["GET"])
async def serve_static(request: Request) -> FileResponse | HTMLResponse:
    """Serve static files from the static directory"""
    filepath = request.path_params.get("filepath", "")

    # Default to index.html if no file specified or if it's a directory
    if not filepath or filepath.endswith("/"):
        filepath = filepath.rstrip("/") + "/index.html" if filepath else "index.html"

    file_path = STATIC_DIR / filepath

    # Security check: ensure the file is within the static directory
    try:
        file_path = file_path.resolve()
        STATIC_DIR.resolve()
        if not str(file_path).startswith(str(STATIC_DIR.resolve())):
            return HTMLResponse("Forbidden", status_code=403)
    except (ValueError, RuntimeError):
        return HTMLResponse("Forbidden", status_code=403)

    # Check if file exists
    if not file_path.is_file():
        return HTMLResponse("Not Found", status_code=404)

    return FileResponse(file_path)


@mcp.custom_route("/", methods=["GET"])
async def root_redirect(request: Request) -> RedirectResponse:
    """Redirect root path to static pages"""
    return RedirectResponse(url="/static/", status_code=302)


# Create ASGI application for production deployment
app = mcp.http_app()
