from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunkText(text, chunkSize=300, chunkOverlap=50):
    """
    Splits long incident text into overlapping chunks before embedding.

    Why this exists: makeIncidentText() concatenates title, symptoms, actions
    tried, recent change info, etc. into one string. That's fine for short
    synthetic incidents, but the sentence-transformers model used in
    embedder.py (all-MiniLM-L6-v2) silently truncates input around ~256
    tokens. A real Freshservice incident (long description HTML, several
    private notes, a full resolution write-up) can easily exceed that, and
    everything past the cutoff would be dropped with no warning. Chunking
    first means every part of the incident gets embedded, not just the
    beginning.
    """
    if not text:
        return [""]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunkSize,
        chunk_overlap=chunkOverlap
    )

    chunks = splitter.split_text(text)

    if len(chunks) == 0:
        return [text]

    return chunks