import numpy as np
from sentence_transformers import SentenceTransformer

from backend.chunking import chunkText


class IncidentEmbedder:
    def __init__(self, chunkSize=300, chunkOverlap=50):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.chunkSize = chunkSize
        self.chunkOverlap = chunkOverlap

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
            actionText = action.get("action") or ""
            result = action.get("result") or ""
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

    def embedChunks(self, chunks):
        vectors = self.model.encode(
            chunks,
            normalize_embeddings=True
        )

        pooled = np.mean(vectors, axis=0)

        norm = np.linalg.norm(pooled)
        if norm > 0:
            pooled = pooled / norm

        return pooled

    def embedIncidents(self, incidents):
        embeddings = []

        for incident in incidents:
            text = self.makeIncidentText(incident)
            chunks = chunkText(text, self.chunkSize, self.chunkOverlap)
            embeddings.append(self.embedChunks(chunks))

        return np.array(embeddings)

    def embedText(self, text):
        chunks = chunkText(text, self.chunkSize, self.chunkOverlap)
        return self.embedChunks(chunks)