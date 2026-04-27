import anthropic

from agent.tools import ALL_TOOLS

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "Use the available tools when they would help answer the user's question. "
    "Be concise in your responses."
)


def create_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def run_agent(client: anthropic.Anthropic, messages: list[dict]) -> str:
    """Run the tool-use agent and return the final text response."""
    runner = client.beta.messages.tool_runner(
        model="claude-opus-4-6",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        tools=ALL_TOOLS,
        messages=messages,
    )

    final_text = ""
    for message in runner:
        for block in message.content:
            if block.type == "text":
                final_text = block.text
            elif block.type == "tool_use":
                print(f"  [tool] {block.name}({block.input})")

    return final_text
