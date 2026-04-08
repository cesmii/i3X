import os
import json
import threading
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_redoc_html
from routers.info import info
from routers.namespaces import ns
from routers.typeDefinitions import typeDefinitions
from routers.objects import explore, query, update
from routers.subscriptions import subs, subscription_worker, handle_data_source_update
from data_sources.factory import DataSourceFactory


# Load configuration helper function
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        return json.load(f)


# Load config to get app settings
config = load_config()
app_config = config.get("app", {})

# Global flag for subscription thread
SUBSCRIPTION_THREAD_FLAG = {"running": True}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Initialize data source(s)
    try:
        # Try new multi-source configuration first
        if "data_sources" in config:
            data_source = DataSourceFactory.create_data_source(config)
            source_types = [
                f"{name}({cfg['type']})" for name, cfg in config["data_sources"].items()
            ]
            print(
                f"Using MULTI-SOURCE configuration with {len(config['data_sources'])} sources: {', '.join(source_types)}"
            )
        else:
            # Fall back to single source configuration
            data_source_config = config.get(
                "data_source", {"type": "mock", "config": {}}
            )
            data_source = DataSourceFactory.create_data_source(data_source_config)
            print(
                f"Using SINGLE-SOURCE configuration: {data_source_config['type'].upper()} data source"
            )
    except Exception as e:
        print(f"Failed to initialize data source(s): {e}")
        print("Falling back to MOCK data source as fallback")
        data_source = DataSourceFactory.create_data_source(
            {"type": "mock", "config": {}}
        )

    # Set the data source in app state
    app.state.data_source = data_source

    # Create callback function that passes subscriptions and data source to the handler
    def callback(instance, value):
        handle_data_source_update(instance, value, app.state.I3X_DATA_SUBSCRIPTIONS, data_source)

    # Start the data source with the callback
    data_source.start(callback)

    # Start subscription worker thread
    threading.Thread(
        target=subscription_worker,
        args=(app.state.I3X_DATA_SUBSCRIPTIONS, SUBSCRIPTION_THREAD_FLAG),
        daemon=True,
    ).start()
    yield
    # Shutdown
    SUBSCRIPTION_THREAD_FLAG["running"] = False

    # Stop the data source
    if hasattr(app.state, "data_source"):
        app.state.data_source.stop()


app = FastAPI(
    title=app_config.get("title", "I3X API"),
    description=app_config.get(
        "description",
        "Industrial Information Interface eXchange API - RFC 001 Compliant",
    ),
    version=app_config.get("version", "1.0.0"),
    root_path=app_config.get("root_path", ""),
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve the favicon."""
    favicon_path = os.path.join(static_dir, "favicon.png")
    return FileResponse(favicon_path, media_type="image/png")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """Custom Swagger UI with icon in header."""
    root_path = app_config.get("root_path", "")
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{app.title} - Docs</title>
        <link rel="icon" type="image/png" href="{root_path}/static/favicon.png">
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({{
                url: "{root_path}{app.openapi_url}",
                dom_id: '#swagger-ui',
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
                layout: "BaseLayout",
                defaultModelsExpandDepth: -1
            }});
        </script>
        <script src="{root_path}/static/swagger-custom.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/redoc", include_in_schema=False)
async def custom_redoc():
    """Custom ReDoc with icon in header."""
    root_path = app_config.get("root_path", "")
    return get_redoc_html(
        openapi_url=f"{root_path}{app.openapi_url}",
        title=app.title + " - ReDoc",
    )

# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": exc.status_code, "message": exc.detail}}
    )


# Setup app state (data source will be set after config is loaded)
app.state.I3X_DATA_SUBSCRIPTIONS = []  # List[Subscription]
app.state.subscription_ttl_seconds = config.get("subscriptions", {}).get("ttl_seconds", 300)
app.state.app_config = app_config
app.state.capabilities_config = config.get("capabilities", {})

# Include routers
app.include_router(info)
app.include_router(ns)
app.include_router(typeDefinitions)
app.include_router(explore)
app.include_router(query)
app.include_router(update)
app.include_router(subs)


if __name__ == "__main__":
    import uvicorn

    config = load_config()
    port = config.get("port", 8080)
    debug = config.get("debug", False)
    host = config.get("host", "0.0.0.0")

    root_path = app_config.get("root_path", "")

    print(f"Starting server on {host}:{port} (debug: {debug})")
    print(f"Swagger page at http://localhost:{port}{root_path}/docs")
    uvicorn.run("app:app", host=host, port=port, reload=debug, root_path=root_path)
