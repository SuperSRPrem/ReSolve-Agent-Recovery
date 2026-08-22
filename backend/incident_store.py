import json


class IncidentStore:
    def __init__(self, filePath="data/incidents.json"):
        self.filePath = filePath
        self.incidents = []
        self.loadIncidents()

    def loadIncidents(self):
        with open(self.filePath, "r") as file:
            self.incidents = json.load(file)

    def getAllIncidents(self):
        return self.incidents

    def getIncident(self, incidentId):
        for incident in self.incidents:
            if incident["incidentId"] == incidentId:
                return incident

        return None

    def saveIncidents(self):
        with open(self.filePath, "w") as file:
            json.dump(self.incidents, file, indent=2)
