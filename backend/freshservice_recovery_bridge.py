from backend.freshservice_ticket_service import (
    FreshserviceTicketService
)

from backend.incident_mapper import (
    mapTicketToIncident
)


class FreshserviceRecoveryBridge:
    """
    Connects Freshservice tickets to the ReSolve
    incident format.

    Responsibilities:

        1. Fetch Freshservice ticket
        2. Fetch ticket conversations
        3. Map ticket into a ReSolve incident

    This class does NOT perform recovery itself.

    The mapped incident can later be passed to:

        DemoAgent
        RecoveryMemory
        VerificationEngine
        RecoverySession
    """

    def __init__(self, ticketService=None):

        self.ticketService = (
            ticketService
            or FreshserviceTicketService()
        )

    def loadIncident(
        self,
        ticketId
    ):
        """
        Loads a Freshservice ticket and converts it
        into the ReSolve incident structure.
        """

        # ==============================================
        # FETCH TICKET
        # ==============================================

        ticketResponse = (
            self.ticketService.getTicket(
                ticketId
            )
        )

        if not ticketResponse.get("success"):

            return {
                "success": False,
                "message": (
                    "Failed to fetch Freshservice ticket."
                ),
                "ticketId": ticketId,
                "incident": None,
                "ticket": None,
                "conversations": [],
                "error": ticketResponse.get("error")
            }

        ticketData = (
            ticketResponse
            .get("data", {})
        )

        ticket = ticketData.get(
            "ticket"
        )

        if not ticket:

            return {
                "success": False,
                "message": (
                    "Freshservice returned no ticket data."
                ),
                "ticketId": ticketId,
                "incident": None,
                "ticket": None,
                "conversations": [],
                "error": None
            }

        # ==============================================
        # FETCH CONVERSATIONS
        # ==============================================

        conversationResponse = (
            self.ticketService.getConversations(
                ticketId
            )
        )

        conversations = []

        conversationError = None

        if conversationResponse.get("success"):

            conversations = (
                conversationResponse
                .get("data", {})
                .get("conversations", [])
            )

        else:

            conversationError = (
                conversationResponse.get(
                    "error"
                )
            )

        # ==============================================
        # MAP → RESOLVE INCIDENT
        # ==============================================

        incident = mapTicketToIncident(
            ticket,
            conversations
        )

        return {
            "success": True,

            "message": (
                "Freshservice ticket successfully "
                "loaded as a ReSolve incident."
            ),

            "ticketId": ticketId,

            "incident": incident,

            "ticket": ticket,

            "conversations": conversations,

            "conversationError": (
                conversationError
            )
        }