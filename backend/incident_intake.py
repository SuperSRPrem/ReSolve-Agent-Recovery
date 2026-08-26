from datetime import datetime, timezone


class IncidentIntake:
    """
    Converts the manual Freshservice-like form into a clean ticket payload.

    Required by the ReSolve manual flow:
        requester_id or requester_email
        subject
        description
        priority
        status

    Everything else is optional and is omitted when empty.
    """

    REQUIRED = (
        "subject",
        "description",
        "priority",
        "status",
    )

    OPTIONAL_FIELD_MAP = {
        "source": "source",
        "category": "category",
        "sub_category": "sub_category",
        "item_category": "item_category",
        "planned_start_date": "planned_start_date",
        "planned_end_date": "planned_end_date",
        "planned_effort": "planned_effort",
        "tags": "tags",
        "urgency": "urgency",
        "impact": "impact",
        "group_id": "group_id",
        "responder_id": "responder_id",
        "agent_id": "responder_id",
        "department_id": "department_id",
        "cc_emails": "cc_emails",
        "workspace_id": "workspace_id",
        "type": "type",
        "custom_fields": "custom_fields",
    }

    @staticmethod
    def _clean(value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        if isinstance(value, list):
            cleaned = [item for item in value if item not in (None, "")]
            return cleaned or None
        return value

    @classmethod
    def validate(cls, form):
        form = form or {}
        errors = []

        for field in cls.REQUIRED:
            if cls._clean(form.get(field)) is None:
                errors.append(f"{field} is required.")

        requester_id = cls._clean(form.get("requester_id"))
        requester_email = cls._clean(
            form.get("requester_email")
            or form.get("email")
        )

        if requester_id is None and requester_email is None:
            errors.append(
                "requester_id or requester_email/email is required."
            )

        return errors

    @classmethod
    def toTicketPayload(cls, form):
        form = dict(form or {})
        errors = cls.validate(form)

        if errors:
            return {
                "success": False,
                "errors": errors,
                "payload": None,
            }

        payload = {
            "subject": cls._clean(form["subject"]),
            "description": cls._clean(form["description"]),
            "priority": int(form["priority"]),
            "status": int(form["status"]),
        }

        requester_id = cls._clean(form.get("requester_id"))
        requester_email = cls._clean(
            form.get("requester_email")
            or form.get("email")
        )

        if requester_id is not None:
            payload["requester_id"] = int(requester_id)
        else:
            payload["email"] = requester_email

        for source, target in cls.OPTIONAL_FIELD_MAP.items():
            value = cls._clean(form.get(source))
            if value is not None:
                payload[target] = value

        payload.setdefault("source", 3)  # Phone, matching the supplied form.
        payload.setdefault("type", "Incident")

        return {
            "success": True,
            "errors": [],
            "payload": payload,
        }

    @staticmethod
    def buildInitialAction(incident):
        actions = incident.get("actionsTried") or []

        if actions:
            latest = actions[-1].get("action")
            if latest:
                return latest

        return "Initial diagnosis did not restore service"

    @staticmethod
    def recoveryMetadata(source):
        return {
            "startedAt": datetime.now(timezone.utc).isoformat(),
            "source": source,
        }
