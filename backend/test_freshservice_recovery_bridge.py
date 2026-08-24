from pprint import pprint

from backend.freshservice_recovery_bridge import (
    FreshserviceRecoveryBridge
)


def main():

    ticketId = 4

    bridge = FreshserviceRecoveryBridge()

    print()
    print("=" * 70)
    print("LOAD FRESHSERVICE INCIDENT INTO RESOLVE")
    print("=" * 70)

    result = bridge.loadIncident(
        ticketId
    )

    print()

    if not result["success"]:

        print("FAILED")

        print()
        print(result["message"])

        print()
        print("Error:")

        pprint(
            result.get("error")
        )

        return

    print("SUCCESS")

    print()
    print(result["message"])

    incident = result["incident"]

    print()
    print("=" * 70)
    print("RESOLVE INCIDENT")
    print("=" * 70)

    pprint(
        incident,
        sort_dicts=False
    )

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(
        "Freshservice Ticket ID:",
        result["ticketId"]
    )

    print(
        "Incident ID:",
        incident["incidentId"]
    )

    print(
        "Title:",
        incident["title"]
    )

    print(
        "Severity:",
        incident["severity"]
    )

    print(
        "Conversations:",
        len(
            result["conversations"]
        )
    )

    print(
        "Actions Tried:",
        len(
            incident["actionsTried"]
        )
    )


if __name__ == "__main__":
    main()