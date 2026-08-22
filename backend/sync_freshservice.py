import json

from backend.freshservice_mcp_client import FreshserviceMCPClient
from backend.incident_mapper import mapTicketToIncident, RESOLVED_STATUSES

OUTPUT_PATH = "data/incidents_from_freshservice.json"


async def _fetchResolvedTickets(session, maxPages=5):
    """
    Pages through get_tickets and keeps only resolved/closed ones.
    Filtering client-side rather than trusting a query string first time
    round - filter_tickets' query syntax is finicky (see the MCP server's
    README) and worth confirming against your real data before relying on
    it in a script.
    """
    allTickets = []

    for page in range(1, maxPages + 1):
        result = await session.call_tool(
            "get_tickets",
            {"page": page, "per_page": 30}
        )

        # result.content is a list of MCP content blocks; the tool's JSON
        # payload is typically in the first block's .text - print(result)
        # once to confirm the exact shape against your installed version
        # before trusting this parsing.
        payload = json.loads(result.content[0].text)
        tickets = payload if isinstance(payload, list) else payload.get("tickets", [])

        if not tickets:
            break

        allTickets.extend(tickets)

    return [t for t in allTickets if t.get("status") in RESOLVED_STATUSES]


def main():
    client = FreshserviceMCPClient()

    print("Available MCP tools (confirm names before relying on this script):")
    for name, description in client.listAvailableTools():
        print(f"  - {name}: {description}")

    resolvedTickets = client.run(_fetchResolvedTickets)
    print(f"\nFetched {len(resolvedTickets)} resolved/closed tickets.")

    incidents = [mapTicketToIncident(ticket) for ticket in resolvedTickets]

    with open(OUTPUT_PATH, "w") as file:
        json.dump(incidents, file, indent=2)

    print(f"Wrote {len(incidents)} incidents to {OUTPUT_PATH}")
    print(
        "Point IncidentStore at this file (or merge it into data/incidents.json) "
        "to run the existing retriever/recovery-memory pipeline on real tickets."
    )


if __name__ == "__main__":
    main()