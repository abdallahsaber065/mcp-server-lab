import json
import logging
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
import litellm

logger = logging.getLogger("mcp_llm_engine")

AVAILABLE_MODELS = [
    # Google Gemini Flash & Flash-Lite Series
    "gemini/gemini-3.1-flash-lite",
    "gemini/gemini-3.5-flash",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-flash-lite",
    "gemini/gemma-4-26b-a4b-it",
    # Mistral AI Models & Free Tier
    "mistral/mistral-small-latest",
    "mistral/open-mistral-7b",
    "mistral/open-mixtral-8x7b",
    "mistral/codestral-latest",
    "mistral/mistral-large-latest",
]

class MCPLLMEngine:
    """Provider-agnostic AI engine using LiteLLM to bridge free LLMs with any MCP server toolset."""

    def __init__(self, default_model: str = "gemini/gemini-2.5-flash"):
        self.default_model = default_model

    async def execute_agent_loop(
        self,
        mcp_server_instance: Any,
        user_message: str,
        system_prompt: str,
        conversation_history: List[Dict[str, Any]],
        model: Optional[str] = None,
        role: str = "property_manager",
        max_rounds: int = 6
    ) -> Dict[str, Any]:
        """Runs non-streaming multi-turn reasoning loop executing MCP tools via LiteLLM."""
        target_model = model if model in AVAILABLE_MODELS else self.default_model
        
        raw_tools = mcp_server_instance.list_tools(role=role)
        formatted_tools = []
        for t in raw_tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["inputSchema"]
                }
            })

        messages = [{"role": "system", "content": system_prompt}] + conversation_history
        messages.append({"role": "user", "content": user_message})

        tool_calls_trace = []
        llm_calls_count = 0

        for round_idx in range(max_rounds):
            llm_calls_count += 1
            
            try:
                kwargs = {
                    "model": target_model,
                    "messages": messages,
                }
                if formatted_tools:
                    kwargs["tools"] = formatted_tools
                    kwargs["tool_choice"] = "auto"

                response = await litellm.acompletion(**kwargs)
            except Exception as e:
                logger.warning(f"LiteLLM call failed for model {target_model}: {e}")
                return {
                    "status": "fallback_executed",
                    "final_answer": f"[Autonomous Engine Response]: Processed request '{user_message}'. Note: Provider API error ({str(e)}), executed defensive boundary fallback.",
                    "tool_calls": tool_calls_trace,
                    "llm_calls": llm_calls_count,
                    "model": target_model
                }

            choice = response.choices[0]
            msg = choice.message
            
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                messages.append(msg)
                for tc in tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}

                    tool_result = mcp_server_instance.call_tool(tool_name, args)
                    tool_calls_trace.append({
                        "round": round_idx + 1,
                        "tool": tool_name,
                        "args": args,
                        "result": tool_result
                    })

                    if tool_result.get("status") == "elicitation_required":
                        return {
                            "status": "elicitation_required",
                            "elicitation_payload": tool_result["elicitation_payload"],
                            "tool_calls": tool_calls_trace,
                            "llm_calls": llm_calls_count,
                            "model": target_model,
                            "messages": messages
                        }

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tool_name,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
            else:
                final_text = msg.content or "Completed operation."
                messages.append({"role": "assistant", "content": final_text})
                return {
                    "status": "success",
                    "final_answer": final_text,
                    "tool_calls": tool_calls_trace,
                    "llm_calls": llm_calls_count,
                    "model": target_model
                }

        return {
            "status": "max_rounds_reached",
            "final_answer": "Max reasoning steps reached without final answer.",
            "tool_calls": tool_calls_trace,
            "llm_calls": llm_calls_count,
            "model": target_model
        }

    async def execute_agent_loop_stream(
        self,
        mcp_server_instance: Any,
        user_message: str,
        system_prompt: str,
        conversation_history: List[Dict[str, Any]],
        model: Optional[str] = None,
        role: str = "property_manager",
        max_rounds: int = 6
    ) -> AsyncGenerator[str, None]:
        """Streams agent reasoning steps, tool calls, and text tokens via SSE formatted data events."""
        target_model = model if model in AVAILABLE_MODELS else self.default_model
        
        raw_tools = mcp_server_instance.list_tools(role=role)
        formatted_tools = []
        for t in raw_tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["inputSchema"]
                }
            })

        messages = [{"role": "system", "content": system_prompt}] + conversation_history
        messages.append({"role": "user", "content": user_message})

        for round_idx in range(max_rounds):
            try:
                kwargs = {
                    "model": target_model,
                    "messages": messages,
                    "stream": True
                }
                if formatted_tools:
                    kwargs["tools"] = formatted_tools
                    kwargs["tool_choice"] = "auto"

                response_stream = await litellm.acompletion(**kwargs)
                
                full_text = ""
                tool_calls_accumulator = {}

                async for chunk in response_stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    
                    content_chunk = getattr(delta, "content", None)
                    if content_chunk:
                        full_text += content_chunk
                        event_payload = json.dumps({"type": "token", "content": content_chunk}, ensure_ascii=False)
                        yield f"data: {event_payload}\n\n"

                    tool_calls_delta = getattr(delta, "tool_calls", None)
                    if tool_calls_delta:
                        for tc in tool_calls_delta:
                            idx = getattr(tc, "index", 0)
                            if idx not in tool_calls_accumulator:
                                tool_calls_accumulator[idx] = {
                                    "id": getattr(tc, "id", None) or f"call_{idx}_{int(time.time()*1000)}",
                                    "name": "",
                                    "arguments": ""
                                }
                            
                            fn = getattr(tc, "function", None)
                            if fn:
                                fn_name = getattr(fn, "name", None)
                                if fn_name:
                                    tool_calls_accumulator[idx]["name"] += fn_name
                                fn_args = getattr(fn, "arguments", None)
                                if fn_args:
                                    tool_calls_accumulator[idx]["arguments"] += fn_args

                if tool_calls_accumulator:
                    assistant_msg = {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": v["id"],
                                "type": "function",
                                "function": {"name": v["name"], "arguments": v["arguments"]}
                            }
                            for v in tool_calls_accumulator.values()
                        ]
                    }
                    messages.append(assistant_msg)

                    for v in tool_calls_accumulator.values():
                        tool_name = v["name"]
                        if not tool_name:
                            continue
                        try:
                            args = json.loads(v["arguments"]) if v["arguments"] else {}
                        except Exception:
                            args = {}

                        tool_result = mcp_server_instance.call_tool(tool_name, args)
                        
                        tool_event = json.dumps({
                            "type": "tool_call",
                            "tool": tool_name,
                            "args": args,
                            "result": tool_result
                        }, ensure_ascii=False)
                        yield f"data: {tool_event}\n\n"

                        if tool_result.get("status") == "elicitation_required":
                            el_event = json.dumps({
                                "type": "elicitation_required",
                                "payload": tool_result["elicitation_payload"]
                            }, ensure_ascii=False)
                            yield f"data: {el_event}\n\n"
                            yield f"data: {json.dumps({'type': 'done'})}\n\n"
                            return

                        messages.append({
                            "role": "tool",
                            "tool_call_id": v["id"],
                            "name": tool_name,
                            "content": json.dumps(tool_result, ensure_ascii=False)
                        })
                else:
                    if full_text:
                        messages.append({"role": "assistant", "content": full_text})
                    done_event = json.dumps({"type": "done", "final_answer": full_text}, ensure_ascii=False)
                    yield f"data: {done_event}\n\n"
                    return

            except Exception as e:
                logger.warning(f"LiteLLM stream failed for model {target_model}: {e}")
                fallback_event = json.dumps({
                    "type": "fallback",
                    "content": f"[Autonomous Engine Response]: Processed request '{user_message}'. Note: Provider API error ({str(e)}), executed defensive boundary fallback."
                }, ensure_ascii=False)
                yield f"data: {fallback_event}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return
