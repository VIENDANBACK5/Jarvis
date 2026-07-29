import json
import time
import uuid
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.registry import get_agent_registry
from backend.services.llm import get_llm

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


def create_chunk(chat_id: str, model: str, content: str, finish_reason: Optional[str] = None) -> str:
    """Tạo chunk định dạng Server-Sent Events (SSE) tương thích OpenAI."""
    chunk = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason
            }
        ]
    }
    return f"data: {json.dumps(chunk)}\n\n"


@router.get("/models")
async def list_models():
    """Trả về danh sách model và agent khả dụng tương thích OpenAI."""
    agents = get_agent_registry().list()
    data = []

    # Predefined models
    base_models = [
        "gpt-4o-mini", 
        "qwen2.5:7b-instruct", 
        "deepseek-chat", 
        "qwen2.5-coder:7b", 
        "qwen2.5-coder:32b", 
        "llama3.3:70b", 
        "deepseek-r1:8b"
    ]
    for m in base_models:
        data.append({
            "id": m,
            "object": "model",
            "created": 1677610602,
            "owned_by": "system"
        })

    # Registered agents as models
    for agent_name in agents:
        data.append({
            "id": agent_name,
            "object": "model",
            "created": 1677610602,
            "owned_by": "jarvis-agents"
        })

    return {"object": "list", "data": data}


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Xử lý hội thoại chat tương thích OpenAI."""
    chat_id = f"chatcmpl-{uuid.uuid4()}"
    model = request.model
    last_message = request.messages[-1].content
    
    agent_registry = get_agent_registry()
    
    # 1. Trường hợp Model là Agent đăng ký trong hệ thống
    if model in agent_registry.list():
        try:
            agent = agent_registry.get(model)
            # Run the agent
            result = await agent.run(last_message)
            response_text = result.get("output") or result.get("plan") or "No output generated."
            
            if request.stream:
                async def agent_stream_generator():
                    # Stream kết quả của Agent (Chia nhỏ văn bản để giả lập stream)
                    chunk_size = 5
                    for i in range(0, len(response_text), chunk_size):
                        chunk = response_text[i:i + chunk_size]
                        yield create_chunk(chat_id, model, chunk)
                        time.sleep(0.01) # Small delay for smooth stream
                    yield create_chunk(chat_id, model, "", "stop")
                    yield "data: [DONE]\n\n"
                    
                return StreamingResponse(agent_stream_generator(), media_type="text/event-stream")
            else:
                return {
                    "id": chat_id,
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_text
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi thực thi Agent: {str(e)}")

    # 2. Trường hợp gọi trực tiếp LLM Model
    try:
        llm = get_llm(model_id=model, temperature=request.temperature)
        
        # Chuyển đổi định dạng message sang dạng LangChain
        lc_messages = []
        for msg in request.messages:
            lc_messages.append((msg.role, msg.content))
            
        if request.stream:
            async def llm_stream_generator():
                async for chunk in llm.astream(lc_messages):
                    yield create_chunk(chat_id, model, chunk.content)
                yield create_chunk(chat_id, model, "", "stop")
                yield "data: [DONE]\n\n"
                
            return StreamingResponse(llm_stream_generator(), media_type="text/event-stream")
        else:
            response = await llm.ainvoke(lc_messages)
            return {
                "id": chat_id,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.content
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi gọi LLM: {str(e)}")
