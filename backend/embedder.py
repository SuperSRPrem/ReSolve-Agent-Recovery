from sentence_transformers import SentenceTransformer


class IncidentEmbedder:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def makeIncidentText(self, incident):
        symptoms = ", ".join(incident.get("symptoms", []))
        errorCodes = ", ".join(incident.get("errorCodes", []))

        if errorCodes == "":
            errorCodes = "None"

        change = incident.get("recentChange", {})
        changeType = change.get("type", "none")
        changeDesc = change.get("description", "None")
        changeTime = change.get("minutesBeforeIncident")

        if changeTime is None:
            changeTime = "Not applicable"

        actions = []

        for action in incident.get("actionsTried", []):
            actionText = action.get("action", "")
            result = action.get("result", "")
            actions.append(actionText + " - " + result)

        if len(actions) == 0:
            actionText = "None"
        else:
            actionText = ", ".join(actions)

        metrics = incident.get("metrics", {})
        latency = metrics.get("apiLatencyMs", "Unknown")
        cpu = metrics.get("databaseCpuPercent", "Unknown")

        text = (
            "Title: " + incident.get("title", "") + "\n"
            "Service: " + incident.get("service", "") + "\n"
            "Environment: " + incident.get("environment", "") + "\n"
            "Severity: " + incident.get("severity", "") + "\n"
            "Symptoms: " + symptoms + "\n"
            "Error codes: " + errorCodes + "\n"
            "API latency: " + str(latency) + " ms\n"
            "Database CPU: " + str(cpu) + "%\n"
            "Recent change type: " + str(changeType) + "\n"
            "Recent change: " + str(changeDesc) + "\n"
            "Minutes before incident: " + str(changeTime) + "\n"
            "Actions already tried: " + actionText
        )

        return text

    def embedIncidents(self, incidents):
        texts = []

        for incident in incidents:
            texts.append(self.makeIncidentText(incident))

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True
        )

        return embeddings

    def embedText(self, text):
        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding
