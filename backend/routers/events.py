
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..services.logger_service import sse_stream
router = APIRouter()
@router.get("", response_class=StreamingResponse)
async def events():
    return StreamingResponse(sse_stream(), media_type="text/event-stream")
