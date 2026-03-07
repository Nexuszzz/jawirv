"""
JAWIR OS - FastAPI Main Application
Entry point for the backend server.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.websocket import ConnectionManager, handle_websocket_message
from app.api.upload import router as upload_router
from app.api.monitoring import router as monitoring_router
from app.api.iot import router as iot_router
from agent.api_rotator import init_rotator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("jawir")

# WebSocket connection manager
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Startup and shutdown events.
    """
    # Startup
    logger.info("🚀 JAWIR OS Backend starting...")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Port: {settings.ws_port}")
    logger.info(f"   Log Level: {settings.log_level}")
    
    # Initialize API Key Rotator
    api_keys = settings.all_google_api_keys
    if api_keys:
        rotator = init_rotator(api_keys)
        logger.info(f"   🔑 API Keys: {len(api_keys)} keys loaded for rotation")
    else:
        logger.warning("   ⚠️ No Google API keys configured!")
    
    # Initialize IoT MQTT Bridge (if enabled)
    if settings.iot_enabled:
        try:
            from services.iot_bridge import start_iot_bridge
            from services.iot_state import iot_state
            import asyncio
            
            if start_iot_bridge():
                logger.info("   🏠 IoT MQTT Bridge: Connected")
                
                # Setup WebSocket broadcast callback for real-time IoT updates
                loop = asyncio.get_event_loop()
                
                def ws_broadcast_callback(data: dict):
                    """Thread-safe callback to broadcast IoT updates via WebSocket."""
                    try:
                        asyncio.run_coroutine_threadsafe(manager.broadcast(data), loop)
                    except Exception as e:
                        logger.error(f"WS broadcast failed: {e}")
                
                iot_state.set_ws_broadcast_callback(ws_broadcast_callback)
                logger.info("   📡 IoT WebSocket broadcast: Enabled")
            else:
                logger.warning("   ⚠️ IoT MQTT Bridge: Failed to connect")
        except Exception as e:
            logger.warning(f"   ⚠️ IoT initialization failed: {e}")
    else:
        logger.info("   ℹ️ IoT: Disabled (IOT_ENABLED=false)")
    
    yield
    
    # Shutdown
    logger.info("👋 JAWIR OS Backend shutting down...")
    
    # Stop IoT bridge
    if settings.iot_enabled:
        try:
            from services.iot_bridge import stop_iot_bridge
            stop_iot_bridge()
        except Exception:
            pass


# Create FastAPI application
app = FastAPI(
    title="JAWIR OS",
    description="Just Another Wise Intelligent Resource - Desktop AI Agent",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router)
app.include_router(monitoring_router)

# Include IoT router (conditional on IoT enabled)
if settings.iot_enabled:
    app.include_router(iot_router)
    logger.info("IoT API routes registered")


# ============================================
# HTTP Endpoints
# ============================================

@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint - API info."""
    return {
        "name": "JAWIR OS",
        "version": "0.1.0",
        "description": "Desktop AI Agent dengan True Agentic Workflow",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "api": True,
            "gemini_configured": len(settings.all_google_api_keys) > 0,
            "tavily_configured": bool(settings.tavily_api_key),
            "iot_enabled": settings.iot_enabled,
        }
    }


@app.get("/health/iot")
async def iot_health_check() -> dict[str, Any]:
    """IoT MQTT Bridge health check endpoint."""
    if not settings.iot_enabled:
        return {
            "status": "disabled",
            "message": "IoT integration is disabled (IOT_ENABLED=false)",
            "timestamp": datetime.now().isoformat(),
        }
    
    try:
        from services.iot_bridge import get_iot_bridge
        from services.iot_state import iot_state
        
        bridge = get_iot_bridge()
        stats = iot_state.get_stats()
        
        return {
            "status": "connected" if bridge and bridge.is_connected() else "disconnected",
            "broker": bridge.get_health() if bridge else None,
            "devices": stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/api/keys/stats")
async def get_api_key_stats() -> dict[str, Any]:
    """Get API key rotation statistics."""
    from agent.api_rotator import get_rotator
    
    rotator = get_rotator()
    if rotator:
        return {
            "status": "active",
            "stats": rotator.get_stats(),
        }
    return {
        "status": "not_initialized",
        "stats": None,
    }


@app.get("/api/config")
async def get_config() -> dict[str, Any]:
    """Get non-sensitive configuration."""
    return {
        "environment": settings.environment,
        "max_retry_count": settings.max_retry_count,
        "max_context_words": settings.max_context_words,
        "deep_research": {
            "breadth": settings.deep_research_breadth,
            "depth": settings.deep_research_depth,
        }
    }


# ============================================
# WebSocket Endpoint
# ============================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Main WebSocket endpoint for chat communication.
    Handles real-time bidirectional messaging with the agent.
    Safe wrapper: NEVER drops connection without sending an error event first.
    """
    await manager.connect(websocket)
    client_id = id(websocket)
    logger.info(f"🔌 Client connected: {client_id}")
    
    try:
        # Send welcome message
        await manager.send_json(websocket, {
            "type": "connection",
            "status": "connected",
            "message": "Selamat datang di JAWIR OS! Silakan ketik atau bicara untuk memulai.",
            "timestamp": datetime.now().isoformat(),
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            logger.debug(f"📩 Received from {client_id}: {data}")
            
            # Safe handler: catch all exceptions during message processing
            try:
                await handle_websocket_message(websocket, manager, data)
            except Exception as handler_err:
                # CRITICAL: Send structured error BEFORE the connection might die
                logger.error(f"❌ Handler error for {client_id}: {handler_err}", exc_info=True)
                try:
                    await manager.send_json(websocket, {
                        "type": "error",
                        "message": f"Terjadi kesalahan internal: {str(handler_err)[:200]}",
                        "recoverable": True,
                        "timestamp": datetime.now().isoformat(),
                    })
                    # Reset status to idle so UI doesn't stay stuck
                    await manager.send_json(websocket, {
                        "type": "agent_status",
                        "status": "idle",
                        "message": "",
                        "details": {},
                        "timestamp": datetime.now().isoformat(),
                    })
                except Exception:
                    # If we can't even send the error, the WS is dead
                    logger.error(f"Failed to send error event to {client_id}")
                    break
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"🔌 Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}", exc_info=True)
        # Try to send error before disconnect
        try:
            await manager.send_json(websocket, {
                "type": "error",
                "message": f"Koneksi WebSocket error: {str(e)[:200]}",
                "recoverable": False,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception:
            pass
        manager.disconnect(websocket)


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.is_development else "An error occurred",
        }
    )


# ============================================
# Run with uvicorn
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.ws_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
