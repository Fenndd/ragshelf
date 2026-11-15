# data/

Local documents and everything derived from them. Only this file is tracked by Git: the documents are third-party copyrighted material, and the derived files (extracted text, chunks, embeddings, logs) contain their text.

| Path | Contents |
| --- | --- |
| `inbox/` | Documents queued for ingestion: one folder per document with the file and `metadata.json` (`authors`, `year`). Nothing reads it now: the prototype's ingestion script was removed, and `ragshelf ingest` is planned in [T009](../tasks/T009-ingest-command.md). |
| `library/` | Ingested documents, one `article_<N>/` folder each: copy of the document, `metadata.json`, `chunks.json`, `embeddings.npy`, `references.txt`, processing logs. Read by `store/dynamic_vector_store.py`. |
| `index/` | Reserved for persisted vector indexes (currently empty). |
| `raw/` | Collected originals not yet queued for ingestion. |
| `experiments/chunking/` | Per-document outputs of the removed prototype script `chunk_experiment.py`, kept as reference. |
| `experiments/problem-cases/` | Documents on which extraction, reference splitting, or clustering failed, grouped by the problem observed. |
