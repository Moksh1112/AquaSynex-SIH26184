import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

clients = set()

async def broadcast_event(event_data: str):
    for queue in clients:
        await queue.put(event_data)

@router.get("/events/stream")
async def events_stream():
    queue = asyncio.Queue()
    clients.add(queue)

    async def event_generator():
        try:
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            clients.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
