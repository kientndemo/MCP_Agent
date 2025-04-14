import json
import asyncio
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from config import DEFAULT_MODEL_ID, SYSTEM_PROMPT, SQL_GENERATION_PROMPT
import logging

logger = logging.getLogger(__name__)

async def generate_sql_for_prompt(
    query: str,
    client: AsyncOpenAI,
    model: str,
    sql_tool_schema: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Calls the LLM to determine if a SQL query is needed and generates it.

    Args:
        query: The user's query.
        client: The OpenAI client.
        model: The model ID to use.
        sql_tool_schema: The schema definition for the sql_query tool.

    Returns:
        A dictionary with 'query' and 'params' if SQL is needed, None otherwise.
    """
    prompt = SQL_GENERATION_PROMPT.format(
        query=query,
        sql_tool_schema=json.dumps(sql_tool_schema, indent=2)
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an SQL generation assistant."},
                {"role": "user", "content": prompt}
            ],
            tools=[sql_tool_schema],
            tool_choice={"type": "function", "function": {"name": "sql_query"}},
            temperature=0,
            max_tokens=500
        )

        message = response.choices[0].message

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            if tool_call.function.name == "sql_query":
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    if 'query' in arguments:
                        logger.info(f"Generated SQL query: {arguments.get('query')}")
                        return {
                            "query": arguments.get('query'),
                            "params": arguments.get('params', {})
                        }
                    else:
                        logger.warning("SQL generation tool call missing 'query' argument.")
                        return None
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse tool call arguments: {tool_call.function.arguments}")
                    return None
            else:
                logger.warning(f"SQL generation model called unexpected tool: {tool_call.function.name}")
                return None
        else:
            content = message.content.strip() if message.content else ""
            if "NO_QUERY" in content:
                logger.info("SQL generation determined no query needed.")
                return None
            else:
                logger.warning(f"SQL generation returned unexpected content: {content}")
                return None

    except Exception as e:
        logger.error(f"Error during SQL generation call: {e}")
        return None

async def agent_loop(
    query: str,
    tools: dict,
    client: AsyncOpenAI,
    messages: List[dict],
    model: str = DEFAULT_MODEL_ID,
    db_context: Optional[str] = None
):
    agent_tools = {k: v for k, v in tools.items() if k != 'sql_query'} if db_context else tools
    tool_schemas = [t["schema"] for t in agent_tools.values()] if agent_tools else None
    tool_names = " and ".join(agent_tools.keys()) if agent_tools else "no tools"

    system_message_content = SYSTEM_PROMPT.format(
        db_context=db_context if db_context is not None else "No database context provided.",
        tools=tool_names
    )
    logger.info(f"Agent Loop System Prompt (first 300 chars): {system_message_content[:300]}...")
    logger.debug(f"Full Agent Loop System Prompt: {system_message_content}")

    agent_messages = [
        {"role": "system", "content": system_message_content}
    ]
    agent_messages.extend([m for m in messages if m['role'] != 'system'])

    current_user_message = {"role": "user", "content": query}
    if not agent_messages or agent_messages[-1] != current_user_message:
        if agent_messages and agent_messages[-1]['role'] == 'user':
             agent_messages.pop()
        agent_messages.append(current_user_message)

    logger.info(f"Calling agent LLM with {len(agent_messages)} messages.")
    logger.debug(f"Agent messages for LLM call: {agent_messages}")
    logger.debug(f"Agent tools for LLM call: {list(agent_tools.keys())}")

    response = await client.chat.completions.create(
        model=model,
        messages=agent_messages,
        tools=tool_schemas,
        max_tokens=4096,
        temperature=0,
    )

    response_message = response.choices[0].message
    stop_reason = response.choices[0].finish_reason
    logger.info(f"Agent LLM response stop reason: {stop_reason}")
    if response_message.content:
        logger.info(f"Agent LLM response content (first 100 chars): {response_message.content[:100]}...")
    if response_message.tool_calls:
        logger.info(f"Agent LLM requested tool calls: {[tc.function.name for tc in response_message.tool_calls]}")

    if response_message.content:
        agent_messages.append({"role": "assistant", "content": response_message.content})

    if response_message.tool_calls:
        stop_reason = "tool_calls"
        assistant_message_with_tools = {
            "role": response_message.role,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in response_message.tool_calls
            ]
        }
        agent_messages.append(assistant_message_with_tools)

        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            if tool_name in agent_tools:
                arguments = json.loads(tool_call.function.arguments)
                callable_tool = agent_tools[tool_name]["callable"]
                logger.info(f"Agent calling tool: {tool_name} with args: {arguments}")
                try:
                    if asyncio.iscoroutinefunction(callable_tool):
                        tool_result = await callable_tool(**arguments)
                    else:
                        tool_result = await asyncio.to_thread(callable_tool, **arguments)
                    logger.info(f"Tool {tool_name} result: {tool_result}")
                    agent_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": json.dumps(tool_result),
                        }
                    )
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    agent_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": json.dumps({"error": f"Failed to execute tool: {e}"}),
                        }
                    )
            else:
                logger.warning(f"Agent tried to call unavailable tool: {tool_name}")
                agent_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps({"error": f"Tool {tool_name} is not available in the current context."}),
                    }
                )

        final_response = await client.chat.completions.create(
            model=model,
            messages=agent_messages,
        )
        final_message_content = final_response.choices[0].message.content
        agent_messages.append({"role": "assistant", "content": final_message_content})
        return final_message_content, agent_messages

    elif stop_reason == "stop":
        final_message_content = response_message.content
        if not agent_messages or agent_messages[-1].get('role') != 'assistant':
            agent_messages.append({"role": "assistant", "content": final_message_content})
        return final_message_content, agent_messages
    else:
        logger.error(f"Unhandled stop reason: {stop_reason}")
        raise ValueError(f"Unknown stop reason: {stop_reason}")