from pprint import pprint

from backend.LLM_Integration.llm_output_normalizer import (
    LLMOutputNormalizer
)


def main():

    print()
    print("=" * 70)
    print("TEST: LLM OUTPUT NORMALIZER")
    print("=" * 70)

    normalizer = LLMOutputNormalizer()

    # ==================================================
    # INCIDENT TEST
    # ==================================================

    rawIncidentData = {
        "service": "  API   ",
        "environment": " PRODUCTION ",

        "symptoms": [
            "Users cannot access the API",
            "Users cannot access the API ",
            "",
            None,
            " HTTP 503 errors "
        ],

        "errorCodes": [
            "503",
            "HTTP 503",
            "http-503",
            "",
            None
        ],

        "actionsTried": [
            {
                "action": " Restart API ",
                "result": "FAILED"
            },
            {
                "action": "restart api",
                "result": "failed"
            },
            {
                "action": "",
                "result": "success"
            },
            {
                "action": "Check logs",
                "result": "something-invalid"
            }
        ],

        "likelyRootCause": "  "
    }

    print()
    print("=" * 70)
    print("TEST 1: INCIDENT NORMALIZATION")
    print("=" * 70)

    print()
    print("RAW DATA:")

    pprint(
        rawIncidentData
    )

    normalizedIncident = (
        normalizer.normalizeIncident(
            rawIncidentData
        )
    )

    print()
    print("NORMALIZED DATA:")

    pprint(
        normalizedIncident
    )

    # ==================================================
    # RESOLUTION TEST
    # ==================================================

    rawResolutionData = {
        "rootCause": (
            " Incorrect deployment configuration "
        ),

        "resolutionAction": (
            " Roll back deployment "
        ),

        "resolutionSteps": [
            "Identify bad deployment",
            "Identify bad deployment ",
            "",
            None,
            "Roll back deployment",
            "Restart API"
        ],

        "result": "COMPLETED",

        "resolutionTimeMinutes": -20
    }

    print()
    print("=" * 70)
    print("TEST 2: RESOLUTION NORMALIZATION")
    print("=" * 70)

    print()
    print("RAW DATA:")

    pprint(
        rawResolutionData
    )

    normalizedResolution = (
        normalizer.normalizeResolution(
            rawResolutionData
        )
    )

    print()
    print("NORMALIZED DATA:")

    pprint(
        normalizedResolution
    )


if __name__ == "__main__":
    main()