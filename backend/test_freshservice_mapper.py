from pprint import pprint

from backend.freshservice_ticket_service import (
    FreshserviceTicketService
)

from backend.incident_mapper import (
    mapTicketToIncident
)


def main():

    ticketId = 4

    service = FreshserviceTicketService()

    print()
    print("=" * 70)
    print("STEP 1: FETCH FRESHSERVICE TICKET")
    print("=" * 70)

    ticketResponse = service.getTicket(
        ticketId
    )

    if not ticketResponse.get("success"):

        print()
        print("Failed to fetch ticket.")

        pprint(ticketResponse)

        return

    ticket = (
        ticketResponse
        .get("data", {})
        .get("ticket")
    )

    if not ticket:

        print()
        print(
            "Ticket response succeeded but "
            "no ticket data was returned."
        )

        pprint(ticketResponse)

        return

    print()
    print("Ticket fetched successfully.")

    print()
    print("Subject:")
    print(ticket.get("subject"))

    # ==================================================
    # FETCH CONVERSATIONS
    # ==================================================

    print()
    print("=" * 70)
    print("STEP 2: FETCH TICKET CONVERSATIONS")
    print("=" * 70)

    conversationResponse = (
        service.getConversations(
            ticketId
        )
    )

    conversations = []

    if conversationResponse.get("success"):

        conversations = (
            conversationResponse
            .get("data", {})
            .get("conversations", [])
        )

        print()
        print(
            "Conversations found:",
            len(conversations)
        )

    else:

        print()
        print(
            "Conversation fetch failed."
        )

        pprint(conversationResponse)

    # ==================================================
    # MAP TO RESOLVE INCIDENT
    # ==================================================

    print()
    print("=" * 70)
    print("STEP 3: MAP TO RESOLVE INCIDENT")
    print("=" * 70)

    incident = mapTicketToIncident(
        ticket,
        conversations
    )

    print()

    pprint(incident, sort_dicts=False)

    print()
    print("=" * 70)
    print("MAPPING COMPLETE")
    print("=" * 70)

    print()

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
        "Actions tried:",
        len(
            incident["actionsTried"]
        )
    )

    print(
        "Freshservice Ticket ID:",
        incident["freshservice"]["ticketId"]
    )


if __name__ == "__main__":
    main()