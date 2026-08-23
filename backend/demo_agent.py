from backend.recovery_memory import RecoveryMemory
from backend.feedback import FeedbackManager
from backend.outcome_tracker import computeErrorSignature
from backend.mock_environment import MockEnvironment
from backend.verification_engine import VerificationEngine
from backend.recovery_session import RecoverySession


class DemoAgent:
    """
    Closed-loop recovery agent.

    Flow:

    Incident
        ↓
    Retrieve strategies
        ↓
    Select next untried strategy
        ↓
    Risk gate
        ↓
    Execute
        ↓
    Verify
        ↓
    Recovered? ── Yes → STOP
        │
        No
        ↓
    Observe updated attempt history
        ↓
    Select next strategy
        ↓
    Repeat
    """

    def __init__(
        self,
        environment=None,
        maxRecoveryAttempts=5
    ):
        self.memory = RecoveryMemory()
        self.feedback = FeedbackManager()
        self.verification = VerificationEngine()

        self.environment = (
            environment
            if environment is not None
            else MockEnvironment()
        )

        self.maxRecoveryAttempts = maxRecoveryAttempts

    def getApprovalStatus(self, riskTier):
        """
        Low-risk actions can execute automatically.

        Medium and high-risk actions pause until
        explicit human approval is received.
        """

        if riskTier == "low":
            return {
                "approved": True,
                "status": "auto-approved"
            }

        return {
            "approved": False,
            "status": "approval-required"
        }

    def startRecovery(self, incident, firstAction):
        """
        Starts a new recovery session.
        """

        errorSignature = computeErrorSignature(incident)

        session = RecoverySession(
            incident,
            errorSignature,
            firstAction
        )

        self.feedback.addAttempt(
            incident,
            firstAction,
            "failed",
            errorSignature
        )

        return self.continueRecovery(session)

    def continueRecovery(self, session):
        """
        Continues recovery until one of these happens:

        1. System is recovered.
        2. Human approval is required.
        3. No reliable strategy remains.
        4. Maximum recovery attempts reached.
        """

        while (
            session.recoveryAttempts
            < self.maxRecoveryAttempts
        ):

            recovery = self.memory.getRecovery(
                session.incident,
                session.attemptHistory
            )

            if recovery["status"] == "NO_MATCH":
                session.status = "ESCALATED"

                return self._buildResult(
                    session,
                    "ESCALATED",
                    (
                        "No additional reliable recovery "
                        "strategy was found."
                    ),
                    reason="NO_MATCH"
                )

            choice = recovery["bestChoice"]

            action = choice["action"]

            approval = self.getApprovalStatus(
                choice["riskTier"]
            )

            # ----------------------------------------------
            # Human approval required
            # ----------------------------------------------

            if not approval["approved"]:

                session.setPendingStrategy(choice)

                session.addAttempt(
                    action,
                    "pending-approval",
                    (
                        f"{choice['riskTier'].capitalize()} risk "
                        "strategy requires human approval."
                    )
                )

                return self._buildResult(
                    session,
                    "AWAITING_APPROVAL",
                    (
                        "Recovery is paused until human "
                        "approval is provided."
                    ),
                    strategy=choice,
                    approval=approval
                )

            # ----------------------------------------------
            # Automatically approved action
            # ----------------------------------------------

            result = self._executeAndVerify(
                session,
                choice
            )

            if result["recovered"]:
                session.status = "RECOVERED"

                return self._buildResult(
                    session,
                    "RECOVERED",
                    (
                        "System recovery was automatically "
                        "verified."
                    ),
                    strategy=choice,
                    execution=result["execution"],
                    verification=result["verification"]
                )

            # Action failed or verification failed.
            # Loop continues and RecoveryMemory selects
            # another untried strategy.

        session.status = "ESCALATED"

        return self._buildResult(
            session,
            "ESCALATED",
            (
                "Maximum safe recovery attempts reached "
                "without verified recovery."
            ),
            reason="MAX_ATTEMPTS_REACHED"
        )

    def approvePendingStrategy(self, session):
        """
        Executes the strategy that was previously paused
        for human approval.

        After execution, verification happens automatically.

        If it fails, the agent continues searching for the
        next available strategy.
        """

        if session.pendingStrategy is None:
            return self._buildResult(
                session,
                "NO_PENDING_APPROVAL",
                "There is no strategy waiting for approval."
            )

        choice = session.pendingStrategy

        session.clearPendingStrategy()

        result = self._executeAndVerify(
            session,
            choice
        )

        if result["recovered"]:
            session.status = "RECOVERED"

            return self._buildResult(
                session,
                "RECOVERED",
                (
                    "Approved recovery strategy executed "
                    "and recovery was verified."
                ),
                strategy=choice,
                execution=result["execution"],
                verification=result["verification"]
            )

        # The approved action failed verification.
        # Continue the autonomous recovery loop.

        return self.continueRecovery(session)

    def rejectPendingStrategy(self, session):
        """
        Rejects the pending strategy.

        The rejected action is recorded as rejected and the
        agent continues searching for another strategy.
        """

        if session.pendingStrategy is None:
            return self._buildResult(
                session,
                "NO_PENDING_APPROVAL",
                "There is no strategy waiting for approval."
            )

        choice = session.pendingStrategy

        session.addAttempt(
            choice["action"],
            "rejected",
            "Human rejected this recovery strategy."
        )

        session.clearPendingStrategy()

        return self.continueRecovery(session)

    def _executeAndVerify(self, session, choice):
        """
        Executes one strategy and automatically verifies
        the resulting system state.
        """

        action = choice["action"]

        execution = self.environment.executeAction(
            action
        )

        session.recoveryAttempts += 1

        executionStatus = execution[
            "executionStatus"
        ]

        # ----------------------------------------------
        # Execution itself failed
        # ----------------------------------------------

        if executionStatus != "success":

            session.addAttempt(
                action,
                "failed",
                execution["message"]
            )

            self.feedback.addAttempt(
                session.incident,
                action,
                "failed",
                session.errorSignature
            )

            self.feedback.recordResult(
                choice["incidentId"],
                session.errorSignature,
                "failed"
            )

            return {
                "recovered": False,
                "execution": execution,
                "verification": None
            }

        # ----------------------------------------------
        # Automatic verification
        # ----------------------------------------------

        verification = self.verification.verify(
            session.incident,
            self.environment.getState()
        )

        verifiedResult = (
            "success"
            if verification["recovered"]
            else "failed"
        )

        session.addAttempt(
            action,
            verifiedResult,
            verification["message"],
            verification
        )

        self.feedback.addAttempt(
            session.incident,
            action,
            verifiedResult,
            session.errorSignature
        )

        self.feedback.recordResult(
            choice["incidentId"],
            session.errorSignature,
            verifiedResult
        )

        return {
            "recovered": verification["recovered"],
            "execution": execution,
            "verification": verification
        }

    def _buildResult(
        self,
        session,
        status,
        message,
        strategy=None,
        approval=None,
        execution=None,
        verification=None,
        reason=None
    ):
        """
        Builds a consistent result object for every stage
        of the recovery lifecycle.
        """

        result = {
            "status": status,
            "message": message,
            "errorSignature": session.errorSignature,
            "attempts": session.attemptHistory,
            "recoveryAttempts": session.recoveryAttempts,
            "environmentState": self.environment.getState(),
            "session": session
        }

        if strategy is not None:
            result["strategy"] = strategy

        if approval is not None:
            result["approval"] = approval

        if execution is not None:
            result["execution"] = execution

        if verification is not None:
            result["verification"] = verification

        if reason is not None:
            result["reason"] = reason

        return result