from backend.recovery_memory import RecoveryMemory
from backend.feedback import FeedbackManager
from backend.outcome_tracker import computeErrorSignature
from backend.mock_environment import MockEnvironment
from backend.verification_engine import VerificationEngine


class DemoAgent:
    """
    Closed-loop recovery demo agent.

    Flow:
    1. Initial action fails.
    2. Retrieve ranked recovery strategies.
    3. Select the next untried strategy.
    4. Apply risk gate.
    5. Execute approved strategy.
    6. Verify actual system state.
    7. If verification fails, try Plan B.
    8. After two failed recovery attempts, escalate.
    """

    def __init__(self, environment=None):
        self.memory = RecoveryMemory()
        self.feedback = FeedbackManager()
        self.verification = VerificationEngine()

        self.environment = (
            environment
            if environment is not None
            else MockEnvironment()
        )

    def getApprovalStatus(self, riskTier):
        """
        Determines whether a strategy may execute automatically.

        Low risk:
            Auto-approved.

        Medium / High:
            Requires human approval.

        UI approval will be connected later.
        """

        if riskTier == "low":
            return {
                "approved": True,
                "status": "auto-approved",
            }

        return {
            "approved": False,
            "status": "approval-required",
        }

    def runIncident(self, incident, firstAction):
        errorSignature = computeErrorSignature(incident)

        attemptHistory = [
            {
                "action": firstAction,
                "result": "failed",
                "errorSignature": errorSignature,
                "note": (
                    "Initial host agent action failed before "
                    "recovery memory was consulted."
                ),
            }
        ]

        self.feedback.addAttempt(
            incident,
            firstAction,
            "failed",
            errorSignature,
        )

        maxRecoveryAttempts = 2
        recoveryAttempts = 0

        while recoveryAttempts < maxRecoveryAttempts:

            recovery = self.memory.getRecovery(
                incident,
                attemptHistory,
            )

            if recovery["status"] == "NO_MATCH":
                return {
                    "status": "ESCALATED",
                    "reason": "NO_MATCH",
                    "message": (
                        "No reliable recovery strategy was found. "
                        "Escalating to human support."
                    ),
                    "errorSignature": errorSignature,
                    "attempts": attemptHistory,
                    "environmentState": self.environment.getState(),
                }

            choice = recovery["bestChoice"]

            action = choice["action"]

            approval = self.getApprovalStatus(
                choice["riskTier"]
            )

            # --------------------------------------------------
            # Approval gate
            # --------------------------------------------------

            if not approval["approved"]:

                attemptHistory.append({
                    "action": action,
                    "result": "pending-approval",
                    "errorSignature": errorSignature,
                    "note": (
                        f"{choice['riskTier'].capitalize()} risk "
                        "strategy requires human approval."
                    ),
                })

                return {
                    "status": "AWAITING_APPROVAL",
                    "message": (
                        "Recovery strategy requires human approval "
                        "before execution."
                    ),
                    "strategy": choice,
                    "approval": approval,
                    "errorSignature": errorSignature,
                    "attempts": attemptHistory,
                    "environmentState": self.environment.getState(),
                }

            # --------------------------------------------------
            # Execute strategy
            # --------------------------------------------------

            execution = self.environment.executeAction(
                action
            )

            recoveryAttempts += 1

            executionResult = execution[
                "executionStatus"
            ]

            # --------------------------------------------------
            # Execution failed
            # --------------------------------------------------

            if executionResult != "success":

                attemptHistory.append({
                    "action": action,
                    "result": "failed",
                    "errorSignature": errorSignature,
                    "note": execution["message"],
                })

                self.feedback.addAttempt(
                    incident,
                    action,
                    "failed",
                    errorSignature,
                )

                self.feedback.recordResult(
                    choice["incidentId"],
                    errorSignature,
                    "failed",
                )

                continue

            # --------------------------------------------------
            # Automatic verification
            # --------------------------------------------------

            verification = self.verification.verify(
                incident,
                self.environment.getState(),
            )

            verificationResult = (
                "success"
                if verification["recovered"]
                else "failed"
            )

            attemptHistory.append({
                "action": action,
                "result": verificationResult,
                "errorSignature": errorSignature,
                "note": verification["message"],
                "verification": verification,
            })

            self.feedback.addAttempt(
                incident,
                action,
                verificationResult,
                errorSignature,
            )

            self.feedback.recordResult(
                choice["incidentId"],
                errorSignature,
                verificationResult,
            )

            # --------------------------------------------------
            # Recovery verified
            # --------------------------------------------------

            if verification["recovered"]:

                return {
                    "status": "RECOVERED",
                    "message": (
                        "Recovery action executed and system "
                        "recovery was automatically verified."
                    ),
                    "recoveryAction": action,
                    "sourceIncident": choice["incidentId"],
                    "strategy": choice,
                    "approval": approval,
                    "execution": execution,
                    "verification": verification,
                    "errorSignature": errorSignature,
                    "attempts": attemptHistory,
                    "environmentState": (
                        self.environment.getState()
                    ),
                }

            # Verification failed.
            # The loop will request the next strategy.
            # Failed actions are automatically excluded by
            # RecoveryMemory.

        return {
            "status": "ESCALATED",
            "reason": "RECOVERY_ATTEMPTS_EXHAUSTED",
            "message": (
                "Recovery strategies were attempted but system "
                "recovery could not be verified. "
                "Escalating to human support."
            ),
            "errorSignature": errorSignature,
            "attempts": attemptHistory,
            "environmentState": self.environment.getState(),
        }