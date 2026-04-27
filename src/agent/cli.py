import sys

from dotenv import load_dotenv

from agent.client import create_client, run_agent


def main() -> None:
    load_dotenv()

    client = create_client()
    messages: list[dict] = []

    print("Claude Tool Agent (type 'quit' to exit)\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            response_text = run_agent(client, messages)
        except Exception as e:
            print(f"\nError: {e}\n")
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": response_text})
        print(f"\nAssistant: {response_text}\n")


if __name__ == "__main__":
    main()
