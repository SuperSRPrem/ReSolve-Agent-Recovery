from backend.LLM_Integration.llm_client import LLMClient


def main():

    print()

    print("=" * 70)
    print("TEST: GEMINI LLM CLIENT")
    print("=" * 70)

    client = LLMClient()

    prompt = """
You are testing an incident analysis system.

Return a short answer to this question:

What is the likely issue if a production API
is returning HTTP 503 errors?
"""

    print()
    print("SENDING PROMPT...")
    print()

    result = client.generate(
        prompt
    )

    print("=" * 70)
    print("RESULT")
    print("=" * 70)

    print()

    if result["success"]:

        print(
            result["text"]
        )

    else:

        print(
            "LLM REQUEST FAILED"
        )

        print()

        print(
            result["error"]
        )


if __name__ == "__main__":

    main()