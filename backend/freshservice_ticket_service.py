import json

from backend.freshservice_mcp_client import (
    FreshserviceMCPClient
)


class FreshserviceTicketService:
    """
    High-level Freshservice ticket operations.

    This class hides raw MCP tool names and MCP response
    structures from the rest of the ReSolve system.

    Other components should use methods like:

        getTickets()
        getTicket()
        getConversations()
        addNote()
        updateTicket()
        resolveTicket()
        createTicket()

    instead of directly calling MCP tools.
    """

    def __init__(self, client=None):

        self.client = (
            client
            or FreshserviceMCPClient()
        )

    # ==================================================
    # RESPONSE NORMALIZATION
    # ==================================================

    def _normalizeResponse(
        self,
        response,
        toolName
    ):
        """
        Converts raw MCP responses into a predictable format.

        Every method in this service should return:

        {
            "success": True / False,
            "tool": "...",
            "data": ...,
            "error": None / "..."
        }
        """

        if response is None:
            return {
                "success": False,
                "tool": toolName,
                "data": None,
                "error": "Freshservice returned no response."
            }

        # --------------------------------------------------
        # If FreshserviceMCPClient already returns a
        # normalized response, preserve it.
        # --------------------------------------------------

        if isinstance(response, dict):

            if "success" in response:

                response.setdefault(
                    "tool",
                    toolName
                )

                response.setdefault(
                    "data",
                    None
                )

                response.setdefault(
                    "error",
                    None
                )

                return response

            # Raw dictionary response.
            return {
                "success": True,
                "tool": toolName,
                "data": response,
                "error": None
            }

        # --------------------------------------------------
        # MCP CallToolResult handling
        # --------------------------------------------------

        isError = getattr(
            response,
            "is_error",
            False
        )

        content = getattr(
            response,
            "content",
            None
        )

        if content:

            parsedContent = []

            for item in content:

                text = getattr(
                    item,
                    "text",
                    None
                )

                if text is None:
                    continue

                parsedContent.append(
                    self._parseTextContent(text)
                )

            if len(parsedContent) == 1:
                data = parsedContent[0]
            else:
                data = parsedContent

            error = self._extractError(
                data
            )

            if isError or error:

                return {
                    "success": False,
                    "tool": toolName,
                    "data": data,
                    "error": (
                        error
                        or "Freshservice MCP tool execution failed."
                    )
                }

            return {
                "success": True,
                "tool": toolName,
                "data": data,
                "error": None
            }

        # --------------------------------------------------
        # Structured MCP content fallback
        # --------------------------------------------------

        structuredContent = getattr(
            response,
            "structured_content",
            None
        )

        if structuredContent is not None:

            return {
                "success": not isError,
                "tool": toolName,
                "data": structuredContent,
                "error": (
                    "Freshservice MCP tool execution failed."
                    if isError
                    else None
                )
            }

        # --------------------------------------------------
        # Final fallback
        # --------------------------------------------------

        return {
            "success": not isError,
            "tool": toolName,
            "data": str(response),
            "error": (
                "Freshservice MCP tool execution failed."
                if isError
                else None
            )
        }

    def _parseTextContent(
        self,
        text
    ):
        """
        Freshservice MCP tools frequently return JSON
        inside TextContent.

        Convert JSON strings into Python dictionaries
        or lists when possible.
        """

        if not isinstance(text, str):
            return text

        cleanedText = text.strip()

        if not cleanedText:
            return ""

        try:
            return json.loads(
                cleanedText
            )

        except json.JSONDecodeError:
            return cleanedText

    def _extractError(
        self,
        data
    ):
        """
        Looks for common error structures returned by
        Freshservice or the MCP server.
        """

        if isinstance(data, dict):

            if data.get("error"):
                return str(
                    data["error"]
                )

            if data.get("message") and (
                data.get("code")
                or data.get("status")
                or data.get("statusCode")
            ):
                return str(
                    data["message"]
                )

            if data.get("code") in [
                "access_denied",
                "unauthorized",
                "forbidden",
                "not_found"
            ]:
                return str(
                    data.get(
                        "message",
                        data["code"]
                    )
                )

        return None

    def _call(
        self,
        toolName,
        arguments=None
    ):
        """
        Internal wrapper used by all Freshservice
        operations.
        """

        try:

            response = self.client.callTool(
                toolName,
                arguments or {}
            )

            return self._normalizeResponse(
                response,
                toolName
            )

        except Exception as error:

            return {
                "success": False,
                "tool": toolName,
                "data": None,
                "error": str(error)
            }

    # ==================================================
    # FETCH TICKETS
    # ==================================================

    def getTickets(
        self,
        page=1,
        perPage=30
    ):

        return self._call(
            "get_tickets",
            {
                "page": page,
                "per_page": perPage
            }
        )

    def getTicket(
        self,
        ticketId
    ):

        return self._call(
            "get_ticket_by_id",
            {
                "ticket_id": ticketId
            }
        )

    # ==================================================
    # CONVERSATIONS
    # ==================================================

    def getConversations(
        self,
        ticketId
    ):

        return self._call(
            "list_all_ticket_conversation",
            {
                "ticket_id": ticketId
            }
        )

    # ==================================================
    # NOTES
    # ==================================================

    def addNote(
        self,
        ticketId,
        body
    ):

        return self._call(
            "create_ticket_note",
            {
                "ticket_id": ticketId,
                "body": body
            }
        )

    # ==================================================
    # UPDATE TICKET
    # ==================================================

    def updateTicket(
        self,
        ticketId,
        ticketFields
    ):

        return self._call(
            "update_ticket",
            {
                "ticket_id": ticketId,
                "ticket_fields": ticketFields
            }
        )

    # ==================================================
    # RESOLVE TICKET
    # ==================================================

    def resolveTicket(
        self,
        ticketId
    ):
        """
        Freshservice status:

            4 = Resolved
            5 = Closed
        """

        return self.updateTicket(
            ticketId,
            {
                "status": 4
            }
        )

    # ==================================================
    # CREATE TICKET
    # ==================================================

    def createTicket(
        self,
        subject,
        description,
        source=2,
        priority=3,
        status=2,
        email=None,
        requesterId=None,
        customFields=None
    ):

        arguments = {
            "subject": subject,
            "description": description,
            "source": source,
            "priority": priority,
            "status": status
        }

        if email is not None:

            arguments["email"] = email

        if requesterId is not None:

            arguments[
                "requester_id"
            ] = requesterId

        if customFields is not None:

            arguments[
                "custom_fields"
            ] = customFields

        return self._call(
            "create_ticket",
            arguments
        )