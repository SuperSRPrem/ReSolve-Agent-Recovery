from backend.retriever import IncidentRetriever


def leaveOneOutReport(topK=3):
    """
    Self-retrieval sanity check: for each incident, treat it as a query and see
    what the retriever finds among the *other* incidents. No manual labels
    needed. Use this to eyeball whether RecoveryMemory's minScore (currently
    0.5) is set sensibly for your real data, and as a quick demo of retrieval
    quality without needing an OpenAI key or an LLM judge.
    """
    retriever = IncidentRetriever()
    incidents = retriever.incidents

    rows = []

    for incident in incidents:
        results = retriever.getSimilarIncidents(incident, limit=topK + 1)
        results = [
            r for r in results
            if r["incident"]["incidentId"] != incident["incidentId"]
        ]

        topScore = results[0]["score"] if results else None
        topMatchId = results[0]["incident"]["incidentId"] if results else None
        topMatchTitle = results[0]["incident"]["title"] if results else None

        rows.append({
            "incidentId": incident["incidentId"],
            "title": incident["title"],
            "topMatchId": topMatchId,
            "topMatchTitle": topMatchTitle,
            "topMatchScore": topScore
        })

    return rows


def precisionRecallAtK(labeledPairs, k=3, minScore=0.5):
    """
    labeledPairs: list of dicts, e.g.
        [{"queryIncidentId": "INC-1247", "relevantIncidentIds": ["INC-1198"]}]

    You fill labeledPairs in by hand once you know (from reading the data, or
    from real recurring incidents) which incidents *should* match each other.
    Same idea as Precision@K / Recall@K in a standard IR eval, scoped to this
    dataset instead of a generic benchmark, and using RecoveryMemory's actual
    scoring path rather than a separate offline metric.
    """
    retriever = IncidentRetriever()
    store = {
        incident["incidentId"]: incident
        for incident in retriever.incidents
    }

    report = []

    for pair in labeledPairs:
        queryIncident = store.get(pair["queryIncidentId"])

        if queryIncident is None:
            continue

        results = retriever.getSimilarIncidents(queryIncident, limit=k + 1)
        results = [
            r for r in results
            if r["incident"]["incidentId"] != queryIncident["incidentId"]
        ]
        results = [r for r in results if r["score"] >= minScore][:k]

        retrievedIds = [r["incident"]["incidentId"] for r in results]
        relevantIds = set(pair["relevantIncidentIds"])

        truePositives = len([rid for rid in retrievedIds if rid in relevantIds])

        precision = truePositives / len(retrievedIds) if retrievedIds else 0.0
        recall = truePositives / len(relevantIds) if relevantIds else 0.0

        report.append({
            "queryIncidentId": pair["queryIncidentId"],
            "retrieved": retrievedIds,
            "relevant": list(relevantIds),
            "precisionAtK": precision,
            "recallAtK": recall
        })

    return report


if __name__ == "__main__":
    print("=== Leave-one-out retrieval sanity check ===")

    for row in leaveOneOutReport():
        print(row)