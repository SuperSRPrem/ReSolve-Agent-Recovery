from backend.freshservice_mcp_client import (
    FreshserviceMCPClient
)


def printSchema(client, toolName):

    print()
    print("=" * 70)
    print(toolName)
    print("=" * 70)

    schema = client.getToolSchema(toolName)

    if schema is None:
        print("Tool not found.")
        return

    print()
    print("Description:")
    print(schema["description"])

    print()
    print("Input Schema:")
    print(schema["inputSchema"])


def main():

    client = FreshserviceMCPClient()

    toolsToInspect = [

        # Read ticket
        "get_ticket_by_id",

        # Read all ticket conversations
        "list_all_ticket_conversation",

        # Add ReSolve progress notes
        "create_ticket_note",

        # Update / resolve / escalate ticket
        "update_ticket",

        # Create escalation ticket if needed
        "create_ticket",

        # Useful for syncing incidents later
        "get_tickets",
    ]

    for toolName in toolsToInspect:

        printSchema(
            client,
            toolName
        )


if __name__ == "__main__":
    main()