from pprint import pprint

from backend.LLM_Integration.reasoning_service import (
    ReasoningService
)


def main():

    print()
    print("=" * 70)
    print("TEST: REASONING SERVICE")
    print("=" * 70)

    service = ReasoningService()

    # ==================================================
    # TEST CURRENT INCIDENT
    # ==================================================

    currentIncident = {
        "title": (
            "Production API returning 503 errors"
        ),

        "description": (
            "Users are unable to access the production "
            "application. The API is returning HTTP 503 "
            "errors. The API service appears unavailable. "
            "A restart was attempted earlier but did not "
            "resolve the problem."
        )
    }

    print()
    print("=" * 70)
    print("TEST 1: CURRENT INCIDENT UNDERSTANDING")
    print("=" * 70)

    currentResult = (
        service.understandIncident(
            currentIncident
        )
    )

    print()
    print(
        "Success:",
        currentResult["success"]
    )

    print()
    print("Structured Incident:")

    pprint(
        currentResult["data"]
    )

    # ==================================================
    # TEST HISTORICAL RESOLUTION
    # ==================================================

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

    print()
    print("=" * 70)
    print("TEST 2: HISTORICAL INCIDENT UNDERSTANDING")
    print("=" * 70)

    historicalResult = (
        service.understandHistoricalIncident(
            historicalIncident
        )
    )

    print()
    print(
        "Success:",
        historicalResult["success"]
    )

    print()
    print("Incident Understanding:")

    pprint(
        historicalResult[
            "incident"
        ]["data"]
    )

    print()
    print("Resolution Understanding:")

    pprint(
        historicalResult[
            "resolution"
        ]["data"]
    )


if __name__ == "__main__":
    main()