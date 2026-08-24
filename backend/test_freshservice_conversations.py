from backend.freshservice_ticket_service import (
    FreshserviceTicketService
)


def main():

    service = FreshserviceTicketService()

    ticketId = 4

    print()
    print("=" * 70)
    print("TEST: FETCH TICKET CONVERSATIONS")
    print("=" * 70)

    print()
    print("Ticket ID:", ticketId)

    result = service.getConversations(
        ticketId
    )

    print()
    print("RAW RESPONSE")
    print("-" * 70)

    print(result)

    if not result.get("success"):

        print()
        print("FAILED TO FETCH CONVERSATIONS")

        print(
            result.get(
                "data"
            )
        )

        return

    print()
    print("=" * 70)
    print("CONVERSATION FETCH SUCCESSFUL")
    print("=" * 70)

    data = result.get("data")

    print()
    print("Response data:")
    print(data)


if __name__ == "__main__":
    main()