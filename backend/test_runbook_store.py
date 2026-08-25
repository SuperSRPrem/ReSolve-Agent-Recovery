from backend.runbook_store import RunbookStore


def main():
    print()
    print("=" * 70)
    print("APPROVED RUNBOOK STORE TEST")
    print("=" * 70)

    store = RunbookStore()

    incident = {
        "incidentId": "CURRENT-DB-001",

        "title": (
            "Production PostgreSQL "
            "database connection refused"
        ),

        "description": (
            "Backend API is unable to connect "
            "to the PostgreSQL database. "
            "Database connection refused."
        ),

        "priority": "high",

        "status": "open",
    }

    candidates = (
        store.getRecoveryCandidates(
            incident
        )
    )

    print(
        "Candidates found:",
        len(candidates)
    )

    for candidate in candidates:
        print()
        print(
            "Runbook:",
            candidate["incidentId"]
        )

        print(
            "Action:",
            candidate["action"]
        )

        print(
            "Evidence score:",
            round(
                candidate["score"],
                4,
            )
        )

        print(
            "Risk:",
            candidate["riskTier"]
        )

        print(
            "Source:",
            candidate["sourceType"]
        )

        print(
            "Historical success rate:",
            candidate["successRate"]
        )

    assert candidates, (
        "Expected an approved runbook "
        "candidate."
    )

    best = candidates[0]

    assert (
        best["action"]
        == "Restart PostgreSQL database"
    )

    print()
    print(
        "PASS: database restart runbook "
        "matched the incident"
    )

    assert (
        best["sourceType"]
        == "approved-runbook"
    )

    print(
        "PASS: candidate provenance "
        "is explicitly runbook evidence"
    )

    assert (
        best["successRate"]
        is None
    )

    assert (
        best[
            "historicalOutcomeAvailable"
        ]
        is False
    )

    print(
        "PASS: no historical success "
        "statistics were fabricated"
    )

    assert (
        best["riskTier"]
        == "medium"
    )

    print(
        "PASS: existing risk tiering "
        "still applies"
    )

    print()
    print("=" * 70)
    print(
        "APPROVED RUNBOOK STORE TEST PASSED"
    )
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
