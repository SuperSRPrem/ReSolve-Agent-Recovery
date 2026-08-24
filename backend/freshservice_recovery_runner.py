from backend.demo_agent import DemoAgent

from backend.freshservice_recovery_bridge import (
    FreshserviceRecoveryBridge
)

from backend.freshservice_recovery_service import (
    FreshserviceRecoveryService
)

from backend.mock_environment import (
    MockEnvironment
)


class FreshserviceRecoveryRunner:
    """
    Connects a Freshservice ticket to the existing
    ReSolve recovery system.

    Flow:

        Freshservice Ticket
                ↓
        FreshserviceRecoveryBridge
                ↓
        ReSolve Incident
                ↓
        FreshserviceRecoveryRunner
                ↓
        DemoAgent
                ↓
        RecoverySession
                ↓
        RecoveryMemory
                ↓
        Recovery Strategy
                ↓
        MockEnvironment
                ↓
        VerificationEngine
                ↓
        FreshserviceRecoveryService
                ↓
        Freshservice Notes / Resolution / Escalation
    """

    def __init__(
        self,
        bridge=None,
        environment=None,
        recoveryService=None,
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

        self.recoveryService = (
            recoveryService
            or FreshserviceRecoveryService()
        )

        self.maxRecoveryAttempts = (
            maxRecoveryAttempts
        )

    # ==================================================
    # CREATE FRESHSERVICE HOOKS
    # ==================================================

    def _createHooks(
        self,
        ticketId
    ):
        """
        Creates lifecycle hooks for one Freshservice
        recovery run.

        DemoAgent remains independent of Freshservice.

        These hooks connect DemoAgent lifecycle events
        to FreshserviceRecoveryService.
        """

        def onRecoveryStarted(session):

            self.recoveryService.recordRecoveryStarted(
                ticketId=ticketId,
                incident=session.incident,
                errorSignature=session.errorSignature
            )

        def onStrategySelected(
            session,
            strategy
        ):

            self.recoveryService.recordStrategySelected(
                ticketId=ticketId,
                strategy=strategy
            )

        def onApprovalRequired(
            session,
            strategy
        ):

            self.recoveryService.recordApprovalRequired(
                ticketId=ticketId,
                strategy=strategy
            )

        def onActionResult(
            session,
            action,
            result,
            verification
        ):

            self.recoveryService.recordActionResult(
                ticketId=ticketId,
                action=action,
                result=result,
                verification=verification
            )

        def onRecoverySuccess(
            session,
            result
        ):

            self.recoveryService.recordRecoverySuccess(
                ticketId=ticketId,
                result=result
            )

        def onRecoveryFailure(
            session,
            result
        ):

            self.recoveryService.recordRecoveryFailure(
                ticketId=ticketId,
                incident=session.incident,
                result=result
            )

        return {
            "onRecoveryStarted": onRecoveryStarted,
            "onStrategySelected": onStrategySelected,
            "onApprovalRequired": onApprovalRequired,
            "onActionResult": onActionResult,
            "onRecoverySuccess": onRecoverySuccess,
            "onRecoveryFailure": onRecoveryFailure
        }

    # ==================================================
    # CREATE RECOVERY AGENT
    # ==================================================

    def _createAgent(
        self,
        ticketId
    ):
        """
        Creates DemoAgent configured with Freshservice
        lifecycle hooks for this ticket.
        """

        hooks = self._createHooks(
            ticketId
        )

        return DemoAgent(
            environment=self.environment,
            maxRecoveryAttempts=(
                self.maxRecoveryAttempts
            ),
            hooks=hooks
        )

    # ==================================================
    # START RECOVERY
    # ==================================================

    def startRecovery(
        self,
        ticketId,
        firstAction
    ):
        """
        Loads a Freshservice ticket and starts
        the ReSolve recovery workflow.
        """

        # ==============================================
        # LOAD FRESHSERVICE INCIDENT
        # ==============================================

        bridgeResult = (
            self.bridge.loadIncident(
                ticketId
            )
        )

        if not bridgeResult.get(
            "success",
            False
        ):

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

        incident = bridgeResult[
            "incident"
        ]

        # ==============================================
        # CREATE AGENT WITH FRESHSERVICE HOOKS
        # ==============================================

        agent = self._createAgent(
            ticketId
        )

        # ==============================================
        # START RECOVERY
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

    # ==================================================
    # APPROVE PENDING STRATEGY
    # ==================================================

    def approvePendingStrategy(
        self,
        ticketId,
        session
    ):
        """
        Continues a paused recovery after
        human approval.

        The new DemoAgent receives the same
        Freshservice lifecycle hooks.
        """

        agent = self._createAgent(
            ticketId
        )

        recoveryResult = (
            agent.approvePendingStrategy(
                session
            )
        )

        recoveryResult[
            "freshserviceTicketId"
        ] = ticketId

        return recoveryResult

    # ==================================================
    # REJECT PENDING STRATEGY
    # ==================================================

    def rejectPendingStrategy(
        self,
        ticketId,
        session
    ):
        """
        Continues recovery after a human rejects
        the currently pending strategy.
        """

        agent = self._createAgent(
            ticketId
        )

        recoveryResult = (
            agent.rejectPendingStrategy(
                session
            )
        )

        recoveryResult[
            "freshserviceTicketId"
        ] = ticketId

        return recoveryResult