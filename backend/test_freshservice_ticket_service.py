from backend.freshservice_ticket_service import (
    FreshserviceTicketService
)


def printSection(title):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main():

    service = FreshserviceTicketService()

    # ==================================================
    # TEST 1
    # List Freshservice tickets
    # ==================================================

    printSection(
        "TEST 1: FETCH FRESHSERVICE TICKETS"
    )

    try:

        result = service.getTickets(
            page=1,
            perPage=5
        )

        print(result)

    except Exception as error:

        print(
            "Failed to fetch tickets:"
        )

        print(error)

        return

    # ==================================================
    # Stop if Freshservice rejected the request
    # ==================================================

    if not result["success"]:

        print()
        print(
            "Freshservice request failed."
        )

        print(
            "Error data:",
            result["data"]
        )

        return

    # ==================================================
    # TEST 2
    # Try to find a ticket ID from the response
    #
    # We don't assume the exact response structure yet.
    # ==================================================

    printSection(
        "TEST 2: INSPECT TICKET RESPONSE"
    )

    data = result["data"]

    print(
        "Ticket response data:"
    )

    print(data)

    # ==================================================
    # For now, we stop here intentionally.
    #
    # We need to inspect the exact structure returned by
    # this MCP server before extracting ticket IDs.
    # ==================================================

    print()
    print(
        "Ticket listing completed successfully."
    )

    print(
        "Next step: inspect this response shape and "
        "extract a real ticket ID."
    )


if __name__ == "__main__":
    main()