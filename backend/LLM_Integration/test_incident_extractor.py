from pprint import pprint

from backend.LLM_Integration.incident_extractor import (
    IncidentExtractor
)


def main():

    print()

    print("=" * 70)
    print("TEST: INCIDENT EXTRACTOR")
    print("=" * 70)

    extractor = IncidentExtractor()

    title = (
        "Production API unavailable"
    )

    description = """
Users are receiving HTTP 503 errors when trying to
access the production API.

The API backend appears unavailable and several users
are unable to use the application.

An engineer restarted the API service earlier, but the
issue continued.

The incident began approximately 20 minutes after a
configuration deployment.
"""

    conversations = [
        {
            "body_text": (
                "Restarting the API service did not resolve "
                "the issue."
            )
        },
        {
            "body_text": (
                "The production environment is affected. "
                "Database connectivity appears normal."
            )
        }
    ]

    print()
    print("EXTRACTING INCIDENT INFORMATION...")
    print()

    result = extractor.extract(
        title=title,
        description=description,
        conversations=conversations
    )

    print("=" * 70)
    print("RESULT")
    print("=" * 70)

    print()

    print(
        "Success:",
        result["success"]
    )

    print()

    print("Structured Data:")

    pprint(
        result["data"]
    )

    if result["error"]:

        print()
        print("Error:")
        print(
            result["error"]
        )

    print()

    print("=" * 70)
    print("RAW LLM RESPONSE")
    print("=" * 70)

    print()

    print(
        result["rawResponse"]
    )


if __name__ == "__main__":

    main()