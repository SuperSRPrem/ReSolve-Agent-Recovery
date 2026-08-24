from backend.recovery_memory import RecoveryMemory
from backend.feedback import FeedbackManager
from backend.outcome_tracker import computeErrorSignature
from backend.mock_environment import MockEnvironment
from backend.verification_engine import VerificationEngine
from backend.recovery_session import RecoverySession
from backend.recovery_record import RecoveryRecordManager


class DemoAgent:
    """
    Closed-loop recovery agent.

    Every recovery run automatically produces a structured
    audit record and readable recovery documentation.
    """

    def __init__(
        self,
        environment=None,
        maxRecoveryAttempts=5,
        hooks=None
    ):
        self.memory = RecoveryMemory()
        self.feedback = FeedbackManager()
        self.verification = VerificationEngine()
        self.recordManager = RecoveryRecordManager()

        self.environment = (
            environment
            if environment is not None
            else MockEnvironment()
        )

        self.maxRecoveryAttempts = (
            maxRecoveryAttempts
        )

        # Optional callbacks a caller (e.g. FreshserviceRecoveryRunner)
        # can supply to react to lifecycle events in real time, without
        # DemoAgent needing to know Freshservice - or any external
        # system - exists. Missing hooks are no-ops, so every existing
        # caller (app.py, the test_*.py scripts) keeps working unchanged.
        #
        # Supported keys, all called as hook(session, ...):
        #   onRecoveryStarted(session)
        #   onStrategySelected(session, strategy)
        #   onApprovalRequired(session, strategy)
        #   onActionResult(session, action, result, verification)
        #   onRecoverySuccess(session, result)
        #   onRecoveryFailure(session, result)
        self.hooks = hooks or {}

    def _fire(self, hookName, *args, **kwargs):
        hook = self.hooks.get(hookName)

        if hook is None:
            return

        try:
            hook(*args, **kwargs)
        except Exception as error:
            # A hook failing (e.g. Freshservice API hiccup) must never
            # break the recovery loop itself - surface it, don't raise.
            print(f"[ReSolve] hook '{hookName}' raised: {error}")

    def getApprovalStatus(self, riskTier):
        if riskTier == "low":
            return {
                "approved": True,
                "status": "auto-approved"
            }

        return {
            "approved": False,
            "status": "approval-required"
        }

    def startRecovery(
        self,
        incident,
        firstAction
    ):
        errorSignature = computeErrorSignature(
            incident
        )

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

        self._fire("onRecoveryStarted", session)

        return self.continueRecovery(
            session
        )

    def continueRecovery(self, session):
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

            choice = recovery[
                "bestChoice"
            ]

            self._fire(
                "onStrategySelected",
                session,
                choice
            )

            action = choice["action"]

            approval = self.getApprovalStatus(
                choice["riskTier"]
            )

            # ==========================================
            # HUMAN APPROVAL GATE
            # ==========================================

            if not approval["approved"]:
                session.setPendingStrategy(
                    choice
                )

                session.addAttempt(
                    action=action,
                    result="pending-approval",
                    note=(
                        f"{choice['riskTier'].capitalize()} "
                        "risk strategy requires human "
                        "approval."
                    ),
                    riskTier=choice["riskTier"],
                    approval=approval,
                    sourceIncident=choice[
                        "incidentId"
                    ],
                    score=choice["score"]
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

            # ==========================================
            # AUTO-APPROVED STRATEGY
            # ==========================================

            result = self._executeAndVerify(
                session,
                choice,
                approval
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
                    execution=result[
                        "execution"
                    ],
                    verification=result[
                        "verification"
                    ]
                )

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

    def approvePendingStrategy(
        self,
        session
    ):
        if session.pendingStrategy is None:
            return self._buildResult(
                session,
                "NO_PENDING_APPROVAL",
                (
                    "There is no strategy waiting "
                    "for approval."
                )
            )

        choice = session.pendingStrategy

        session.clearPendingStrategy()

        approval = {
            "approved": True,
            "status": "human-approved"
        }

        result = self._executeAndVerify(
            session,
            choice,
            approval
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
                execution=result[
                    "execution"
                ],
                verification=result[
                    "verification"
                ]
            )

        return self.continueRecovery(
            session
        )

    def rejectPendingStrategy(
        self,
        session
    ):
        if session.pendingStrategy is None:
            return self._buildResult(
                session,
                "NO_PENDING_APPROVAL",
                (
                    "There is no strategy waiting "
                    "for approval."
                )
            )

        choice = session.pendingStrategy

        session.addAttempt(
            action=choice["action"],
            result="rejected",
            note=(
                "Human rejected this recovery strategy."
            ),
            riskTier=choice["riskTier"],
            approval={
                "approved": False,
                "status": "human-rejected"
            },
            sourceIncident=choice[
                "incidentId"
            ],
            score=choice["score"]
        )

        session.clearPendingStrategy()

        return self.continueRecovery(
            session
        )

    def _executeAndVerify(
        self,
        session,
        choice,
        approval
    ):
        action = choice["action"]

        execution = (
            self.environment.executeAction(
                action
            )
        )

        session.recoveryAttempts += 1

        executionStatus = execution[
            "executionStatus"
        ]

        # ==========================================
        # EXECUTION FAILED
        # ==========================================

        if executionStatus != "success":
            session.addAttempt(
                action=action,
                result="failed",
                note=execution["message"],
                execution=execution,
                riskTier=choice["riskTier"],
                approval=approval,
                sourceIncident=choice[
                    "incidentId"
                ],
                score=choice["score"]
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

            self._fire(
                "onActionResult",
                session,
                action,
                "failed",
                None
            )

            return {
                "recovered": False,
                "execution": execution,
                "verification": None
            }

        # ==========================================
        # VERIFY REAL POST-CONDITIONS
        # ==========================================

        verification = (
            self.verification.verify(
                session.incident,
                self.environment.getState()
            )
        )

        verifiedResult = (
            "success"
            if verification["recovered"]
            else "failed"
        )

        session.addAttempt(
            action=action,
            result=verifiedResult,
            note=verification["message"],
            verification=verification,
            execution=execution,
            riskTier=choice["riskTier"],
            approval=approval,
            sourceIncident=choice[
                "incidentId"
            ],
            score=choice["score"]
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

        self._fire(
            "onActionResult",
            session,
            action,
            verifiedResult,
            verification
        )

        return {
            "recovered": verification[
                "recovered"
            ],
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
        Every result contains an automatically generated
        structured recovery record and readable report.

        Terminal results are persisted to disk.
        """

        environmentState = (
            self.environment.getState()
        )

        recoveryRecord = (
            self.recordManager.buildRecord(
                session=session,
                environmentState=environmentState,
                status=status,
                reason=reason
            )
        )

        documentation = (
            self.recordManager.generateDocumentation(
                recoveryRecord
            )
        )

        # Persist only completed runs.
        if status in [
            "RECOVERED",
            "ESCALATED"
        ]:
            self.recordManager.saveRecord(
                recoveryRecord
            )

        result = {
            "status": status,
            "message": message,
            "runId": session.runId,
            "errorSignature": (
                session.errorSignature
            ),
            "attempts": (
                session.attemptHistory
            ),
            "recoveryAttempts": (
                session.recoveryAttempts
            ),
            "environmentState": (
                environmentState
            ),
            "recoveryRecord": recoveryRecord,
            "documentation": documentation,
            "session": session
        }

        if strategy is not None:
            result["strategy"] = strategy

        if approval is not None:
            result["approval"] = approval

        if execution is not None:
            result["execution"] = execution

        if verification is not None:
            result["verification"] = (
                verification
            )

        if reason is not None:
            result["reason"] = reason

        # Fire the terminal-ish lifecycle hooks here, now that result
        # is fully built. _buildResult is the one place every
        # continueRecovery/approvePendingStrategy return path passes
        # through, so this is the single source of truth for these
        # three - no risk of firing them twice or missing a path.
        if status == "AWAITING_APPROVAL" and strategy is not None:
            self._fire(
                "onApprovalRequired",
                session,
                strategy
            )
        elif status == "RECOVERED":
            self._fire(
                "onRecoverySuccess",
                session,
                result
            )
        elif status == "ESCALATED":
            self._fire(
                "onRecoveryFailure",
                session,
                result
            )

        return result