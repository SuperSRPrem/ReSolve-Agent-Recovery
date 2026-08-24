from backend.freshservice_ticket_service import (
    FreshserviceTicketService
)


def printResult(
    title,
    result
):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    print(result)


def main():

    service = FreshserviceTicketService()

    # ==================================================
    # TEST 1
    # ==================================================

    result = service.getTickets(
        page=1,
        perPage=5
    )

    printResult(
        "TEST 1: FETCH TICKETS",
        result
    )

    # ==================================================
    # STOP IF FRESHSERVICE DENIED ACCESS
    # ==================================================

    if not result.get("success"):

        print()
        print(
            "Freshservice rejected the request."
        )

        print(
            "ReSolve MCP integration is working, "
            "but Freshservice credentials or account "
            "permissions need to be fixed."
        )

        return

    # ==================================================
    # INSPECT RESPONSE
    # ==================================================

    data = result.get("data")

    printResult(
        "TEST 2: RAW TICKET RESPONSE",
        data
    )


if __name__ == "__main__":
    main()