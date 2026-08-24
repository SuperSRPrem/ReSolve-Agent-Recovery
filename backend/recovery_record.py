import json
import os
from datetime import datetime, timezone


class RecoveryRecordManager:
    """
    Builds and stores structured recovery records.

    The structured record is the source of truth.

    Human-readable documentation is generated deterministically
    from that record for now.

    Later, the LLM layer can convert the same structured record
    into a richer post-incident report without changing the
    recovery engine.
    """

    def __init__(self, filePath="data/recovery_records.json"):
        self.filePath = filePath

    def buildRecord(
        self,
        session,
        environmentState,
        status,
        reason=None
    ):
        attempts = []

        for index, attempt in enumerate(
            session.attemptHistory,
            start=1
        ):
            attemptRecord = {
                "attemptNumber": index,
                "action": attempt.get("action", ""),
                "result": attempt.get("result", ""),
                "errorSignature": attempt.get(
                    "errorSignature",
                    session.errorSignature
                ),
                "note": attempt.get("note", "")
            }

            if attempt.get("riskTier") is not None:
                attemptRecord["riskTier"] = attempt[
                    "riskTier"
                ]

            if attempt.get("approval") is not None:
                attemptRecord["approval"] = attempt[
                    "approval"
                ]

            if attempt.get("sourceIncident") is not None:
                attemptRecord["sourceIncident"] = attempt[
                    "sourceIncident"
                ]

            if attempt.get("score") is not None:
                attemptRecord["score"] = attempt["score"]

            if attempt.get("execution") is not None:
                attemptRecord["execution"] = attempt[
                    "execution"
                ]

            if attempt.get("verification") is not None:
                attemptRecord["verification"] = attempt[
                    "verification"
                ]

            attempts.append(attemptRecord)

        record = {
            "runId": session.runId,
            "createdAt": session.createdAt,
            "updatedAt": self.getTimestamp(),
            "incident": self.buildIncidentSummary(
                session.incident
            ),
            "errorSignature": session.errorSignature,
            "status": status,
            "reason": reason,
            "recoveryAttempts": session.recoveryAttempts,
            "attempts": attempts,
            "finalEnvironmentState": environmentState.copy()
        }

        return record

    def buildIncidentSummary(self, incident):
        """
        Keeps the most useful incident fields in the audit record
        without blindly copying the entire source object.
        """

        return {
            "incidentId": incident.get(
                "incidentId",
                ""
            ),
            "title": incident.get(
                "title",
                ""
            ),
            "service": incident.get(
                "service",
                ""
            ),
            "severity": incident.get(
                "severity",
                ""
            ),
            "environment": incident.get(
                "environment",
                ""
            ),
            "symptoms": incident.get(
                "symptoms",
                []
            ),
            "errorCodes": incident.get(
                "errorCodes",
                []
            ),
            "description": incident.get(
                "description",
                ""
            )
        }

    def generateDocumentation(self, record):
        """
        Produces readable documentation from the structured
        recovery record.

        No LLM is required for this version, so the output is
        deterministic and auditable.
        """

        incident = record["incident"]

        lines = []

        lines.append("ReSolve Recovery Report")
        lines.append("=" * 50)

        lines.append(
            f"Run ID: {record['runId']}"
        )

        lines.append(
            f"Incident ID: "
            f"{incident.get('incidentId') or 'Unknown'}"
        )

        lines.append(
            f"Title: "
            f"{incident.get('title') or 'Unknown'}"
        )

        lines.append(
            f"Service: "
            f"{incident.get('service') or 'Unknown'}"
        )

        lines.append(
            f"Severity: "
            f"{incident.get('severity') or 'Unknown'}"
        )

        lines.append(
            f"Error Signature: "
            f"{record['errorSignature']}"
        )

        lines.append(
            f"Final Status: "
            f"{record['status']}"
        )

        if record.get("reason"):
            lines.append(
                f"Reason: {record['reason']}"
            )

        lines.append("")
        lines.append("Recovery Timeline")
        lines.append("-" * 50)

        for attempt in record["attempts"]:
            number = attempt["attemptNumber"]

            lines.append(
                f"Attempt {number}: "
                f"{attempt['action']}"
            )

            lines.append(
                f"  Result: {attempt['result']}"
            )

            if attempt.get("riskTier"):
                lines.append(
                    f"  Risk: "
                    f"{attempt['riskTier']}"
                )

            if attempt.get("approval"):
                approval = attempt["approval"]

                if isinstance(approval, dict):
                    approvalText = approval.get(
                        "status",
                        str(approval)
                    )
                else:
                    approvalText = str(approval)

                lines.append(
                    f"  Approval: "
                    f"{approvalText}"
                )

            if attempt.get("sourceIncident"):
                lines.append(
                    f"  Historical Evidence: "
                    f"{attempt['sourceIncident']}"
                )

            execution = attempt.get("execution")

            if execution:
                lines.append(
                    f"  Execution: "
                    f"{execution.get('executionStatus')}"
                )

                capability = execution.get(
                    "capability"
                )

                if capability:
                    lines.append(
                        f"  Capability: "
                        f"{capability}"
                    )

            verification = attempt.get(
                "verification"
            )

            if verification:
                lines.append(
                    f"  Verification: "
                    f"{verification.get('status')}"
                )

                for check in verification.get(
                    "checks",
                    []
                ):
                    checkStatus = (
                        "PASS"
                        if check.get("passed")
                        else "FAIL"
                    )

                    lines.append(
                        f"    - "
                        f"{check.get('name')}: "
                        f"{checkStatus}"
                    )

            if attempt.get("note"):
                lines.append(
                    f"  Note: {attempt['note']}"
                )

            lines.append("")

        lines.append("Final Environment State")
        lines.append("-" * 50)

        for key, value in record[
            "finalEnvironmentState"
        ].items():
            lines.append(
                f"{key}: {value}"
            )

        return "\n".join(lines)

    def saveRecord(self, record):
        """
        Persists a completed recovery record.

        Existing runIds are replaced instead of duplicated.
        """

        directory = os.path.dirname(
            self.filePath
        )

        if directory:
            os.makedirs(
                directory,
                exist_ok=True
            )

        records = []

        if os.path.exists(self.filePath):
            try:
                with open(
                    self.filePath,
                    "r",
                    encoding="utf-8"
                ) as file:
                    records = json.load(file)

                    if not isinstance(records, list):
                        records = []

            except (
                json.JSONDecodeError,
                OSError
            ):
                records = []

        records = [
            item
            for item in records
            if item.get("runId") != record["runId"]
        ]

        records.append(record)

        with open(
            self.filePath,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                records,
                file,
                indent=2
            )

        return True

    def getTimestamp(self):
        return datetime.now(
            timezone.utc
        ).isoformat()