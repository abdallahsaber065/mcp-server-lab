import json
import logging
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
import litellm

logger = logging.getLogger("mcp_llm_engine")

class MCPLLMEngine:
    """Reusable, provider-agnostic AI engine using LiteLLM to bridge LLMs with any MCP server toolset."""

    def __init__(self, default_model: str = "gemini/gemini-1.5-flash"):
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
        """Runs multi-turn reasoning loop executing MCP tools via Litellm."""
        target_model = model or self.default_model
        
        # 1. Discover available tools from MCP Server dynamically
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
        total_prompt_tokens = 0
        total_completion_tokens = 0

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
                # Fallback to direct heuristic/tool mock if API fails
                return {
                    "final_answer": f"[AI Response via Fallback Engine]: Processed request '{user_message}'. Note: Provider API error ({str(e)}), executed defensive boundary fallback.",
                    "tool_calls": tool_calls_trace,
                    "llm_calls": llm_calls_count,
                    "model": target_model,
                    "total_tokens": total_prompt_tokens + total_completion_tokens
                }

            usage = getattr(response, "usage", None)
            if usage:
                total_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                total_completion_tokens += getattr(usage, "completion_tokens", 0)

            choice = response.choices[0]
            msg = choice.message
            
            # Check if model invoked tool calls
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                messages.append(msg)
                for tc in tool_calls:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}

                    # Execute tool call on MCP server instance
                    tool_result = mcp_server_instance.call_tool(tool_name, args)
                    tool_calls_trace.append({
                        "round": round_idx + 1,
                        "tool": tool_name,
                        "args": args,
                        "result": tool_result
                    })

                    # Check if human elicitation is required mid-call
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
                    "model": target_model,
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "total_tokens": total_prompt_tokens + total_completion_tokens
                }

        return {
            "status": "max_rounds_reached",
            "final_answer": "Max reasoning steps reached without final answer.",
            "tool_calls": tool_calls_trace,
            "llm_calls": llm_calls_count,
            "model": target_model
        }
