import numpy as np

from backend.incident_store import IncidentStore
from backend.embedder import IncidentEmbedder


class IncidentRetriever:
    def __init__(self):
        self.store = IncidentStore()
        self.embedder = IncidentEmbedder()

        self.incidents = self.store.getAllIncidents()
        self.embeddings = self.embedder.embedIncidents(self.incidents)

    def getSimilarIncidents(self, currentIncident, limit=3):
        currentText = self.embedder.makeIncidentText(currentIncident)
        currentEmbedding = self.embedder.embedText(currentText)

        results = []

        for i in range(len(self.incidents)):
            score = np.dot(currentEmbedding, self.embeddings[i])

            result = {
                "incident": self.incidents[i],
                "score": float(score)
            }

            results.append(result)

        results.sort(key=lambda item: item["score"], reverse=True)

        return results[:limit]
