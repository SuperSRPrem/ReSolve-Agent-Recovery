from pprint import pprint

from backend.LLM_Integration.resolution_extractor import (
    ResolutionExtractor
)


def main():

    print()
    print("=" * 70)
    print("TEST: RESOLUTION EXTRACTOR")
    print("=" * 70)

    historicalIncident = {
        "title": (
            "Production API unavailable"
        ),

        "description": (
            "Users were unable to access the production "
            "API and were receiving HTTP 503 errors."
        ),

        "symptoms": [
            "HTTP 503 errors",
            "API unavailable"
        ],

        "actionsTried": [
            {
                "action": (
                    "Restarted API service"
                ),
                "result": "failed"
            },
            {
                "action": (
                    "Restored previous deployment "
                    "configuration"
                ),
                "result": "success"
            }
        ],

        "rootCause": (
            "Incorrect production deployment "
            "configuration"
        ),

        "resolution": {
            "action": (
                "Rolled back to the previous "
                "working deployment configuration"
            ),

            "steps": [
                "Identified the latest deployment",
                "Confirmed the configuration mismatch",
                "Rolled back to the previous deployment",
                "Restarted the API service",
                "Verified successful API responses"
            ],

            "result": "success",

            "resolutionTimeMinutes": 25
        }
    }

    extractor = ResolutionExtractor()

    print()
    print("EXTRACTING RESOLUTION INFORMATION...")
    print()

    result = extractor.extract(
        historicalIncident
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

    print()
    print("=" * 70)
    print("RAW LLM RESPONSE")
    print("=" * 70)

    print()

    print(
        result.get(
            "rawResponse"
        )
    )

    if result.get("error"):

        print()
        print("=" * 70)
        print("ERROR")
        print("=" * 70)

        print(
            result["error"]
        )


if __name__ == "__main__":
    main()