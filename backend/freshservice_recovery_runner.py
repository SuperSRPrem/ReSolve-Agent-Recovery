from backend.demo_agent import DemoAgent
from backend.freshservice_recovery_bridge import (
    FreshserviceRecoveryBridge
)
from backend.mock_environment import MockEnvironment


class FreshserviceRecoveryRunner:
    """
    Connects a real Freshservice ticket to the
    existing ReSolve recovery system.

    Flow:

        Freshservice Ticket
                ↓
        FreshserviceRecoveryBridge
                ↓
        ReSolve Incident
                ↓
        DemoAgent
                ↓
        RecoverySession
                ↓
        RecoveryMemory
                ↓
        Recovery Strategy
    """

    def __init__(
        self,
        bridge=None,
        environment=None,
        maxRecoveryAttempts=5
    ):
        self.bridge = (
            bridge
            or FreshserviceRecoveryBridge()
        )

        self.environment = (
            environment
            or MockEnvironment()
        )

        self.maxRecoveryAttempts = (
            maxRecoveryAttempts
        )

    def startRecovery(
        self,
        ticketId,
        firstAction
    ):
        """
        Loads a Freshservice ticket and starts the
        existing ReSolve recovery flow.
        """

        # ==============================================
        # LOAD FRESHSERVICE INCIDENT
        # ==============================================

        bridgeResult = (
            self.bridge.loadIncident(
                ticketId
            )
        )

        if not bridgeResult["success"]:

            return {
                "success": False,
                "status": "LOAD_FAILED",
                "message": (
                    "Unable to load Freshservice "
                    "ticket into ReSolve."
                ),
                "ticketId": ticketId,
                "error": bridgeResult.get(
                    "error"
                ),
                "bridgeResult": bridgeResult
            }

        incident = bridgeResult["incident"]

        # ==============================================
        # CREATE EXISTING RECOVERY AGENT
        # ==============================================

        agent = DemoAgent(
            environment=self.environment,
            maxRecoveryAttempts=(
                self.maxRecoveryAttempts
            )
        )

        # ==============================================
        # START EXISTING RECOVERY FLOW
        # ==============================================

        recoveryResult = (
            agent.startRecovery(
                incident,
                firstAction
            )
        )

        # ==============================================
        # ATTACH FRESHSERVICE CONTEXT
        # ==============================================

        recoveryResult[
            "freshserviceTicketId"
        ] = ticketId

        recoveryResult[
            "incident"
        ] = incident

        recoveryResult[
            "bridgeResult"
        ] = {
            "conversationCount": len(
                bridgeResult.get(
                    "conversations",
                    []
                )
            )
        }

        return recoveryResult

    def approvePendingStrategy(
        self,
        session
    ):
        """
        Passes human approval to the existing
        ReSolve recovery session.
        """

        agent = DemoAgent(
            environment=self.environment,
            maxRecoveryAttempts=(
                self.maxRecoveryAttempts
            )
        )

        return agent.approvePendingStrategy(
            session
        )