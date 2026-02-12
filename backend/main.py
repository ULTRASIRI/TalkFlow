"""
TalkFlow Main Application
FastAPI backend with WebSocket support for real-time audio processing
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from backend.config import Config
from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.utils.logger import setup_logger
from backend.utils.metrics import MetricsCollector

# Initialize logger
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="TalkFlow", version="1.0.0")

# Global instances
config = Config()
orchestrator: Optional[PipelineOrchestrator] = None
metrics_collector = MetricsCollector()

# Store active connections
active_connections: Dict[str, WebSocket] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize models and pipeline on startup"""
    global orchestrator
    logger.info("Starting TalkFlow application...")
    
    try:
        # Initialize pipeline orchestrator
        orchestrator = PipelineOrchestrator(config)
        await orchestrator.initialize()
        logger.info("Pipeline initialized successfully")
        
        # Log system info
        logger.info(f"Model paths configured:")
        logger.info(f"  - Whisper: {config.WHISPER_MODEL_PATH}")
        logger.info(f"  - Argos: {config.ARGOS_MODEL_PATH}")
        logger.info(f"  - Piper: {config.PIPER_MODEL_PATH}")
        
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down TalkFlow application...")
    if orchestrator:
        await orchestrator.cleanup()


@app.get("/")
async def root():
    """Serve the main HTML page"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    
    if not frontend_path.exists():
        return {"error": "Frontend not found"}
    
    with open(frontend_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pipeline_ready": orchestrator is not None and orchestrator.is_ready,
        "active_connections": len(active_connections)
    }


@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return {
        "source_language": config.SOURCE_LANGUAGE,
        "target_language": config.TARGET_LANGUAGE,
        "vad_enabled": config.VAD_ENABLED,
        "sample_rate": config.SAMPLE_RATE,
        "chunk_duration_ms": config.CHUNK_DURATION_MS
    }


@app.post("/api/config")
async def update_config(settings: dict):
    """Update configuration dynamically"""
    try:
        if "source_language" in settings:
            config.SOURCE_LANGUAGE = settings["source_language"]
        if "target_language" in settings:
            config.TARGET_LANGUAGE = settings["target_language"]
        if "vad_enabled" in settings:
            config.VAD_ENABLED = settings["vad_enabled"]
        
        logger.info(f"Configuration updated: {settings}")
        return {"status": "success", "updated": settings}
    
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return {"status": "error", "message": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio processing"""
    client_id = id(websocket)
    await websocket.accept()
    active_connections[str(client_id)] = websocket
    
    logger.info(f"Client {client_id} connected")
    
    # Send initial connection message
    try:
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "TalkFlow ready"
        })
    except Exception as e:
        logger.error(f"Failed to send connection message: {e}")
        active_connections.pop(str(client_id), None)
        return
    
    try:
        while True:
            # Check if connection is still open
            if websocket.client_state.name != "CONNECTED":
                logger.info(f"Client {client_id} connection closed")
                break
            
            # Receive audio data or control messages
            try:
                data = await websocket.receive()
            except RuntimeError as e:
                # Connection closed
                logger.info(f"Client {client_id} disconnected: {e}")
                break
            
            if "bytes" in data:
                # Process audio bytes
                audio_bytes = data["bytes"]
                await process_audio_stream(websocket, audio_bytes)
                
            elif "text" in data:
                # Handle control messages
                message = json.loads(data["text"])
                await handle_control_message(websocket, message)
            
            else:
                # Connection closed or invalid message
                logger.debug(f"Received message without bytes or text: {data}")
                if "type" in data and data["type"] == "websocket.disconnect":
                    break
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected gracefully")
    
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}", exc_info=True)
    
    finally:
        # Cleanup
        active_connections.pop(str(client_id), None)
        logger.info(f"Client {client_id} connection cleaned up")


async def process_audio_stream(websocket: WebSocket, audio_bytes: bytes):
    """Process incoming audio stream through the pipeline"""
    try:
        # Check if connection is still open
        if websocket.client_state.name != "CONNECTED":
            logger.debug("Skipping processing - connection closed")
            return
        
        # Process through orchestrator
        result = await orchestrator.process_audio(audio_bytes)
        
        if result:
            # Send transcription
            if result.get("transcription"):
                try:
                    await websocket.send_json({
                        "type": "transcription",
                        "text": result["transcription"],
                        "language": result.get("source_language"),
                        "is_final": result.get("is_final", False)
                    })
                except Exception as e:
                    logger.warning(f"Failed to send transcription: {e}")
                    return
            
            # Send translation
            if result.get("translation"):
                try:
                    await websocket.send_json({
                        "type": "translation",
                        "text": result["translation"],
                        "language": result.get("target_language")
                    })
                except Exception as e:
                    logger.warning(f"Failed to send translation: {e}")
                    return
            
            # Send synthesized audio
            if result.get("audio_bytes"):
                try:
                    await websocket.send_bytes(result["audio_bytes"])
                except Exception as e:
                    logger.warning(f"Failed to send audio: {e}")
                    return
            
            # Send metrics
            if result.get("metrics"):
                try:
                    await websocket.send_json({
                        "type": "metrics",
                        "data": result["metrics"]
                    })
                except Exception as e:
                    logger.warning(f"Failed to send metrics: {e}")
                    return
    
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        try:
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to process audio"
                })
        except:
            pass  # Connection already closed


async def handle_control_message(websocket: WebSocket, message: dict):
    """Handle control messages from client"""
    msg_type = message.get("type")
    
    if msg_type == "ping":
        await websocket.send_json({"type": "pong"})
    
    elif msg_type == "reset":
        # Reset pipeline state
        if orchestrator:
            await orchestrator.reset()
        await websocket.send_json({
            "type": "reset_complete",
            "message": "Pipeline reset"
        })
    
    elif msg_type == "get_metrics":
        # Send current metrics
        metrics = metrics_collector.get_summary()
        await websocket.send_json({
            "type": "metrics_summary",
            "data": metrics
        })
    
    else:
        logger.warning(f"Unknown control message type: {msg_type}")


# Mount static files (CSS, JS)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


def main():
    """Run the application"""
    host = os.getenv("TALKFLOW_HOST", "127.0.0.1")
    port = int(os.getenv("TALKFLOW_PORT", "8000"))
    
    logger.info(f"Starting TalkFlow on {host}:{port}")
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,  # Disabled for production
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
