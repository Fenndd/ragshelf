# Document parsing for a local RAG system (state as of November 2026)

Research date: 2026-11-14. Scope: replacing a heuristic PyMuPDF/pdfplumber pipeline (custom column splitter, regex cleaning, heuristic bibliography split) on an RTX 3060 Laptop (6 GB VRAM), 16 GB RAM, Windows 11 without WSL, Python 3.14 + torch 2.14.1+cu130.
Method: about 15 web searches and fetches, mostly primary sources (GitHub READMEs, release pages, changelogs), plus one benchmark aggregator. No software was installed and no weights were downloaded. Facts from vendor-run benchmarks are marked as such.

## Q1. Which parsers and models are state of the art in late 2026? Release dates and maintenance status

### Takeaway
In late 2026 the frontier is held by small (0.9–1.2B) document VLMs: PaddleOCR-VL-1.6 (May 2026) and MinerU2.5-Pro, packaged in toolkits such as MinerU 4.x. Docling is the most actively maintained general framework (releases v2.142–v2.150 between late October and 10 November 2026). GROBID (0.9.1, 2026) is still the specialist for scholarly metadata and references. Granite-Docling-258M dates from 2025, and olmOCR has had no release since October 2025.

### Cited Findings
- **MinerU (OpenDataLab).** Recent releases: 3.0.0 (2026-03-29), 3.1.0 (2026-04-18), 3.3 (2026-06-11, adds an `effort` medium/high setting for the Hybrid backend), 3.4 (2026-06-18, pipeline OCR upgraded to PP-OCRv6). 4.0, 4.1.x and 4.2.x appear later in the changelog without dates. The 2.7.x line ran from 2025-12-30 to 2026-02-06. — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog)
- **MinerU models.** The OmniDocBench README lists the MinerU2.5-Pro (1.2B) VLM as MinerU's strongest entry. MinerU2.5 (1.2B, the "2509" checkpoint) arrived in the 2.5 series in September 2025 (older). — [OmniDocBench GitHub](https://github.com/opendatalab/OmniDocBench); [MinerU2.5 paper, arXiv 2509.22186](https://arxiv.org/pdf/2509.22186v2); [MinerU 2.5.0 release](https://newreleases.io/project/github/opendatalab/MinerU/release/mineru-2.5.0-released)
- **PaddleOCR-VL-1.6 (Baidu).** Released 2026-05-28. Its own release materials report 96.33% on OmniDocBench v1.6, and the official README table shows 96.34. About 0.9B parameters, same architecture as 1.5, so it is a drop-in upgrade. One Chinese article gives 2 June 2026 as the date. — [paddleocr.ai](https://www.paddleocr.ai/latest/en/index.html); [QbitAI, 2026-06](https://www.qbitai.com/2026/06/427754.html); [HF mirror card](https://huggingface.co/npario/PaddleOCR-VL-1.6)
- **PaddleOCR-VL-1.5.** Paper arXiv 2601.21957 (January 2026). It extends language coverage from 109 to 111 languages. — [arXiv 2601.21957](https://arxiv.org/abs/2601.21957); [HackerNoon summary](https://hackernoon.com/paddleocr-vl-15-a-09b-vision-language-ocr-model-built-for-real-world-documents)
- **Docling (IBM / LF AI).** Very active: v2.142.1 (23 Oct), v2.143.0 (26 Oct), v2.145.0 (29 Oct), v2.146.0 (3 Nov), v2.148.0 (5 Nov), v2.149.0 (8 Nov), v2.150.0 (10 Nov 2026). The page omits years, but the sequence implies 2026. Recent additions include VLM presets for Unlimited-OCR 2, LightOnOCR-3, Nemotron 3.5 multi-pass and MiniCPM-OCR, plus iCalendar and iXBRL backends and EPUB fixes. — [Docling releases](https://github.com/docling-project/docling/releases)
- **Granite-Docling-258M (IBM).** Model card release date 17 September 2025 (older), Apache 2.0. It replaced SmolDocling-256M-preview's SmolLM-2 backbone with a Granite 3-based one. IBM planned larger (~512M and ~900M) variants, all to stay under 1B; I found no primary confirmation that these shipped in 2026. One vendor page claims a January 2026 release date, which conflicts with the model card. — [HF model card](https://huggingface.co/ibm-granite/granite-docling-258M); [IBM announcement](https://ibm.com/new/announcements/granite-docling-end-to-end-document-conversion); [InfoQ, Oct 2025](https://www.infoq.com/news/2025/10/granite-docling-ibm); [idp-software vendor page, conflicting](https://idp-software.com/vendors/docling/)
- **Marker (Datalab).** The repo page shows "© 2026" but no release list or version. Its `vllm` mode now uses the Surya 2.5 (0.69B) model, and Datalab's newer Chandra OCR 2 model powers their hosted platform. — [Marker GitHub](https://github.com/datalab-to/marker)
- **olmOCR (AllenAI).** Latest is v0.4.0 (2025-10-21) with olmOCR-2-7B-1025-FP8; no 2026 release appears on the repo page (older). — [olmOCR GitHub](https://github.com/allenai/olmocr)
- **GROBID.** 0.9.0 (7 Apr) and 0.9.1 (4 Aug, labelled latest). The 0.9.1 notes fix CVE-2026-54513, so it is a 2026 release. 0.9.0 is probably 2026 too, but the page shows no year. — [GROBID releases](https://github.com/kermitt2/grobid/releases)
- **PyMuPDF4LLM (Artifex).** March 2026: the layout engine (`pymupdf-layout`) is bundled and enabled by default, with overall layout F1 rising from 0.8343 to 0.8640. July 2026: version 1.28 brings a major table-extraction upgrade. The latest patch is reported as 1.28.2 (August 2026, from third-party listings). — [Artifex: new PyMuPDF4LLM with Layout](https://artifex.com/blog/introducing-the-new-pymupdf4llm-now-including-layout); [Artifex: tables in 1.28](https://artifex.com/blog/enhanced-table-extraction-in-pymupdf4llm-1-28); [NuGet wrapper 1.28.2](https://packages.nuget.org/packages/MuPDF.NET.PDF4LLM/)
- **Other 2026 leaders on OmniDocBench v1.5** (aggregator snapshot): GLM-OCR (94.35), Youtu-Parsing (93.37), Logics-Parsing-v2 (92.56), FireRed-OCR (92.07), DeepSeek-OCR-2 (89.17), Dolphin-v2 (88.71), MonkeyOCR-pro. — [benchmarklist OmniDocBench 1.5](https://benchmarklist.com/benchmarks/omnidocbench_1_5/)
- **TeleOCR** (arXiv 2608.12898, August 2026) evaluates on OmniDocBench v1.6 (1,651 pages, 10 document types, 5 layout types, 5 languages). — [TeleOCR paper](https://arxiv.org/pdf/2608.12898)

### Inferences
- Nougat is no longer a relevant baseline. None of the 2026 leaderboards I checked list it; its role has passed to the sub-2B document VLMs above.
- For maintenance risk, Docling and MinerU are both very active in 2026. GROBID is slower but alive. olmOCR's last release is about a year old.

### Gaps
- Unstructured (open-source `unstructured`) was not researched; I found no 2026 benchmark entry for it. Add it in a follow-up if needed.
- Exact dates for MinerU 4.0–4.2.2 (the changelog shows none). Which MinerU 4.x is current in November 2026 is unverified.
- Whether Granite-Docling 512M/900M variants have shipped by November 2026.
- Marker's current version number.

## Q2. Quality on scientific articles and books: reading order, tables, formulas, headers and footers, footnotes, and the reference list and bibliographic metadata

### Takeaway
On OmniDocBench v1.6 (official README) the leaders are PaddleOCR-VL-1.6 (96.34) and MinerU2.5-Pro (95.75). MinerU's classical pipeline scores 86.47 and Marker 78.44. Docling and PyMuPDF4LLM have no OmniDocBench rows. None of these tools produces parsed references (authors, year, title, DOI); only GROBID does. A March 2026 benchmark recommends GROBID for clean PDFs, escalating to LLMs for multilingual or footnote-heavy documents.

### Cited Findings
**OmniDocBench (official repo).** The benchmark has moved to v1.7 (update log 2026-04-30), but the published end-to-end table is "v1.6_full". Higher is better for Overall, Formula CDM and Table TEDS; lower is better for Text Edit and Read-Order Edit. — [OmniDocBench GitHub](https://github.com/opendatalab/OmniDocBench)

| Model | Type | Overall | Text Edit | Formula CDM | Table TEDS | Read-Order Edit |
|---|---|---|---|---|---|---|
| PaddleOCR-VL-1.6 (0.9B) | VLM | 96.34 | n/a | n/a | n/a | n/a |
| MinerU2.5-Pro (1.2B) | VLM | 95.75 | n/a | n/a | 93.42 | 0.120 |
| PaddleOCR-VL-1.5 | VLM | 94.93 | n/a | n/a | n/a | n/a |
| PaddleOCR-VL (0.9B) | VLM | 94.18 | 0.040 | 95.91 | 90.65 | 0.135 |
| MinerU-2.5 (1.2B) | VLM | 93.04 | 0.045 | 95.77 | 87.88 | 0.130 |
| dots.ocr (3B) | VLM | 90.77 | 0.048 | 89.95 | 87.18 | 0.138 |
| DeepSeek-OCR 2 (3B) | VLM | 90.25 | 0.050 | 91.84 | 83.89 | 0.144 |
| MinerU-Pipeline | Pipeline | 86.47 | 0.055 | 83.07 | 81.88 | 0.153 |
| olmOCR (7B) | VLM | 85.74 | 0.139 | 88.10 | 83.00 | 0.216 |
| Marker | Pipeline | 78.44 | 0.157 | 85.24 | 65.77 | 0.243 |

(n/a: the fetched summary gave only the overall score for that row.)

- The official v1.6 table has no rows for Docling, PyMuPDF4LLM, PP-StructureV3 or granite-docling. Docling and PP-StructureV3 appear only in the evaluated-models list. — [OmniDocBench GitHub](https://github.com/opendatalab/OmniDocBench)
- OmniDocBench v1.5 (aggregator, rows dated 2026-05-28): PaddleOCR-VL-1.5 94.50 (read-order edit 0.042); MinerU2.5 90.93 (0.044); dots.ocr 88.41; DeepSeek-OCR-2 89.17; olmOCR 81.79 (table TEDS 68.92); MinerU2-pipeline 75.51; Marker-1.8.2 71.30 (table TEDS 57.88, read-order edit 0.250). Docling and PyMuPDF are absent. — [benchmarklist OmniDocBench 1.5](https://benchmarklist.com/benchmarks/omnidocbench_1_5/)
- MinerU's own changelog: the 3.0.0 pipeline backend scores 86.2 on OmniDocBench v1.5. Hybrid `effort=medium` loses 0.13 points against `high` on v1.6 while parsing 35–220% faster (3.3). PP-OCRv6 in 3.4 gives about 11% better OCR accuracy on v1.6. — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog)
- **olmOCR-Bench** (AllenAI's benchmark, unit tests on hard PDF features), overall scores: Chandra OCR 0.1.0 83.1, Infinity-Parser 7B 82.5, olmOCR v0.4.0 82.4, PaddleOCR-VL 80.0, Marker 1.10.1 76.1, DeepSeek-OCR 75.7, MinerU 2.5.4 75.2, Mistral OCR 72.0. Per-category, after re-aligning columns that the fetch tool scrambled, so verify against the README:

  | Tool | Tables | Old scans | Headers & footers |
  |---|---|---|---|
  | olmOCR | 84.9 | 47.7 | 96.1 |
  | PaddleOCR-VL | 84.1 | 37.8 | 97.0 |
  | MinerU 2.5.4 | 84.9 | 33.7 | 96.6 |
  | Marker | 72.9 | 33.5 | 86.6 |

  — [olmOCR GitHub](https://github.com/allenai/olmocr)
- **Datalab's OmniParseBench** (Marker's vendor benchmark, 92 languages). Score and speed: MinerU 2.5-Pro 87.1 (0.54 pages/s); Marker `vllm` 85.9 (4.5 pages/s); Marker `balanced` 80.5 (16.9 pages/s); PaddleOCR-VL-1.6 78.7; DeepSeek-OCR-2 75.2; Marker `fast` (CPU) 71.0; docling 67.5 (2.1 pages/s); Chandra OCR 2 90.1. On olmOCR-bench the same page reports docling 50.3, MinerU pipeline 72.7 and Marker `vllm` 83.7. The GPU used for these speeds is not stated in the summary. — [Marker GitHub](https://github.com/datalab-to/marker)
- **PyMuPDF4LLM with Layout.** Layout F1 rose from 0.8343 to 0.8640, with the biggest gains on small regions such as page footers (Artifex's own measurement). — [Artifex blog](https://artifex.com/blog/introducing-the-new-pymupdf4llm-now-including-layout)
- **GROBID reference quality** (0.9.0 benchmarks, CRF models). On eLife, reference_citation reaches P 93.63 / R 91.81 / F1 92.71, while the micro-average over all fields is 72.48 F1. The docs call these figures "a relative indication of error rates" rather than absolute accuracy. The deep-learning models can be more accurate but are slower and need more resources. — [GROBID benchmarking, eLife](https://grobid.readthedocs.io/en/latest/benchmarks/Benchmarking-elife/); [GROBID benchmarking index](https://GROBID.readthedocs.io/en/latest/Benchmarking/)
- GROBID extracts and parses references (citation and reference-segmenter models, the `processCitationList` service). It can consolidate metadata against CrossRef or biblio-glutton (DOI matching) and links footnote callouts (0.7.2). — [GROBID releases](https://github.com/kermitt2/grobid/releases); [biblio-glutton matching accuracy](https://biblio-glutton.readthedocs.io/en/latest/Benchmarking/)
- Older independent comparisons. 2018: GROBID was the best out-of-the-box reference parser (F1 0.89, ahead of CERMINE 0.83 and ParsCit 0.75). 2023: GROBID had the highest cumulative score across extraction tasks, though no tool was best on every element. — [arXiv 1802.01168](https://arxiv.org/pdf/1802.01168); [arXiv 2303.09957](https://arxiv.org/pdf/2303.09957)
- **March 2026 benchmark** (Zhu, Colavizza, Romanello, SCOLIA; arXiv 2603.13651). Covers reference extraction, reference parsing and end-to-end parsing in the social sciences and humanities, with GROBID against DeepSeek-V3.1, Mistral-Small-3.2-24B, Gemma-3-27B and Qwen3-VL. Extraction saturates beyond a moderate model size; parsing stays brittle on noisy layouts. The authors recommend GROBID for well-structured, in-distribution PDFs and task-adapted (LoRA) LLMs for multilingual or footnote-heavy documents. — [arXiv 2603.13651](https://arxiv.org/abs/2603.13651); [Emergent Mind summary](https://www.emergentmind.com/papers/2603.13651)
- A 2025 study found most language models beat GROBID at identifying author surnames (older). — [arXiv 2505.15948 review](https://www.themoonlight.io/review/citation-parsing-and-analysis-with-language-models)
- Docling's recent releases mention JATS license and funding statements and table footnotes, but no bibliography or reference-parsing feature. — [Docling releases](https://github.com/docling-project/docling/releases)

### Inferences
- Reading order is the main weakness of the current heuristic pipeline. On it, the VLM-based tools (MinerU2.5/Pro, PaddleOCR-VL) are clearly better than Marker and the older pipelines: read-order edit about 0.12–0.14 against 0.24 on v1.6. This should remove the need for a custom column splitter.
- Reference lists: general parsers emit references as text blocks, at best labelled as a reference or list section. Structured fields (authors, year, title, DOI) still need GROBID, or an LLM post-parse step over the extracted reference block. A hybrid fits the evidence best: a VLM parser for the body text, plus GROBID `processFulltextDocument` or `processReferences` on the same PDF for the header metadata and bibliography.
- Docling's accuracy relative to MinerU and PaddleOCR is only evidenced by a competitor's (Datalab's) benchmark, where Docling is weaker. Treat that as indicative, not neutral.

### Gaps
- No neutral 2026 benchmark covering Docling (default Heron pipeline) or granite-docling on OmniDocBench v1.6. Also no 2026 GROBID-versus-VLM comparison on STEM papers, as opposed to the SSH corpus.
- No book-specific benchmark found (long documents, running heads, chapter structure); OmniDocBench has a books category, but I did not obtain per-category numbers.
- Footnote handling per tool is not benchmarked in the sources I read.
- The exact metrics in arXiv 2603.13651 were not read from the PDF.

## Q3. Support for other formats (DOCX, EPUB, HTML, Markdown, TXT), scanned PDFs (OCR) and multilingual text (English, Russian, Slovak; Cyrillic OCR)

### Takeaway
Docling and MinerU 4.x both cover the full format set natively (DOCX, EPUB, HTML and more). Marker covers most of it through an optional extra. GROBID and olmOCR are PDF-only, and PyMuPDF4LLM is centred on PDF. Cyrillic OCR is explicitly supported by the PaddleOCR family (PP-OCRv5 in MinerU, PaddleOCR-VL with 109–111 languages) and by Marker's Surya. For Slovak (Latin script with diacritics) I found no tool-specific evidence.

### Cited Findings
- **MinerU 4.0 inputs:** PDF, images, DOC/DOCX, PPT/PPTX, XLS/XLSX, RTF, ODT/ODS/ODP, EPUB, OFD, HTML/MHTML, CSV/TSV. Plain text is read directly. Native DOCX parsing arrived in 3.0.0; PPTX and XLSX in 3.1.0. — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog)
- **MinerU OCR:** PP-OCRv5 multilingual (37 languages including Russian) since 2.1.0. The Cyrillic model was upgraded to PP-OCRv5 in 2.6.2, with over 40% accuracy gain claimed. 3.4 dropped the separate English, Latin, Japanese and Traditional Chinese options in favour of the `ch` model; the effect on Cyrillic is not stated. — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog)
- **Docling inputs:** PDF, DOCX, PPTX, XLSX, HTML, EPUB, LaTeX, plain text, images, email (EML/MSG), audio, video, WebVTT, iCalendar, ODF, XBRL/iXBRL, and mixed-format ZIP. "Extensive OCR support for scanned PDFs and images"; recent releases mention RapidOCR, including page-orientation detection. — [Docling GitHub](https://github.com/docling-project/docling); [Docling releases](https://github.com/docling-project/docling/releases)
- **Granite-Docling** multilingual support is "experimental" (Arabic, Chinese and Japanese named), so it is mainly an English model. — [IBM announcement](https://ibm.com/new/announcements/granite-docling-end-to-end-document-conversion); [HF model card](https://huggingface.co/ibm-granite/granite-docling-258M)
- **PaddleOCR-VL:** 109 languages including Russian (v1.0); 111 in v1.5. — [PaddleOCR-VL mirror](https://cnb.cool/ai-models/PaddlePaddle/PaddleOCR-VL); [HackerNoon on 1.5](https://hackernoon.com/paddleocr-vl-15-a-09b-vision-language-ocr-model-built-for-real-world-documents)
- **Marker inputs:** PDF, images, PPTX, DOCX, XLSX, HTML, EPUB (non-PDF needs `marker-pdf[full]`). It claims "all languages", with OmniParseBench covering 92 languages and OCR via Surya. — [Marker GitHub](https://github.com/datalab-to/marker)
- **GROBID** processes PDFs only (scholarly documents). Language detection options (Lingua, Blingfire) arrived in 0.9.0. — [GROBID releases](https://github.com/kermitt2/grobid/releases)
- **Scans:** on OmniDocBench "Real5" (scans, warping, skew), PaddleOCR-VL-1.6 reports 93.19% (self-reported). — [immers.cloud listing](https://en.immers.cloud/ai/baidu/paddleocr-vl-1.6/)

### Inferences
- Markdown and TXT need no ML parser; a trivial loader suffices. DOCX, EPUB and HTML can be handled by Docling's or MinerU's non-ML backends without GPU use.
- Russian is safest with PaddleOCR-based OCR (MinerU pipeline/hybrid or PaddleOCR-VL). Slovak is Latin-script and should be covered by multilingual OCR, but verify diacritics accuracy on sample pages.

### Gaps
- No per-language accuracy figures for Russian or Slovak in any tool. No evidence on whether MinerU2.5-Pro (the VLM) handles Cyrillic as well as its PP-OCR pipeline.
- Docling's default OCR engine languages and its Cyrillic quality were not confirmed.

## Q4. Resource fit: VRAM/RAM, throughput on 6 GB GPU or CPU, native Windows 11 with Python 3.14 + PyTorch 2.14/CUDA 13.0, dependency weight

### Takeaway
MinerU 4.1+ is the only tool with documented Python 3.14 support (3.11–3.14), native Windows GPU acceleration (lmdeploy since 2.6.5) and a 6 GB-class VRAM minimum, though its ONNX GPU path needs ≥6 GiB dedicated, which is borderline on this GPU. Docling runs natively on Windows (Python ≥3.10; 3.14 not confirmed), and granite-docling at 258M is light. olmOCR is excluded (needs ≥12 GB VRAM). PaddleOCR-VL is small, but its docs push Windows users to WSL or Docker. GROBID is a Java service usually run in Docker.

### Cited Findings
- **MinerU:** 4.1.0 supports Python 3.11–3.14, with CPU inference on Windows, Linux and macOS and GPU acceleration on NVIDIA, AMD, Intel and Apple GPUs. Since 2.6.5, the lmdeploy engine gives native Windows acceleration (vLLM does not). Direct ONNX GPU selection requires ≥6 GiB dedicated memory (4.2.0). The auto-tier for CPU requires 4 logical cores for "Basic" and 12 for "Standard". — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog)
- **MinerU VRAM, older figures:** 2.6.3 notes list Volta or later with ≥6 GB (one column) and ≥8 GB (another); vLLM on Windows only via WSL2. A 2.7.0 README mirror lists minimum VRAM values of 6, 10, 8 and 3 GB across backends without a clear mapping. vlm-sglang ran on 8 GB GPUs (2.1.0). — [MinerU 2.6.3 release](https://newreleases.io/project/github/opendatalab/MinerU/release/mineru-2.6.3-released); [MinerU README mirror](https://gitcode.com/wll/MinerU_7047/blob/master/README.md); [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog)
- **MinerU, practitioner report:** a tutorial on a 48 GB GPU saw VRAM peaks around 25 GB on large multi-page documents. This shows VRAM grows with batch and document size when it is not capped; it is not a minimum. — [sonusahani.com MinerU guide](https://sonusahani.com/blogs/mineru)
- **Docling:** runs on macOS, Linux and Windows (x86_64 and arm64). Python ≥3.10 (3.9 dropped in v2.70.0). Supports local and air-gapped execution. — [Docling GitHub](https://github.com/docling-project/docling)
- **Granite-Docling:** 258M parameters; GGUF quantisations exist. — [HF model card](https://huggingface.co/ibm-granite/granite-docling-258M); [GGUF](https://huggingface.co/Mungert/granite-docling-258M-GGUF)
- **PaddleOCR-VL:** 0.9B. One guide claims 1–2 GB VRAM (unverified; another low-quality source says 4 GB). A mirror advises Windows users to use WSL or Docker, though the HF page has a separate Windows install step. — [insiderllm guide](https://insiderllm.com/guides/paddleocr-vl-local-document-ocr/); [PaddleOCR-VL mirror](https://cnb.cool/ai-models/PaddlePaddle/PaddleOCR-VL); [HF PaddleOCR-VL](https://huggingface.co/paddlepaddle/PaddleOCR-VL)
- **olmOCR:** requires ≥12 GB GPU RAM (tested on RTX 4090, L40S, A100, H100) and 30 GB of disk; Windows not mentioned. — [olmOCR GitHub](https://github.com/allenai/olmocr)
- **Marker:** Python 3.10+ and PyTorch. Docker plus the NVIDIA Container Toolkit for NVIDIA GPUs; llama.cpp `llama-server` for CPU. Speeds: `fast` CPU mode 23.6 pages/s at score 71.0, `balanced` 16.9 pages/s, `vllm` 4.5 pages/s (vendor hardware not stated). VRAM and Windows are not documented. — [Marker GitHub](https://github.com/datalab-to/marker)
- **GROBID:** Java (JDK 21 and Gradle 9 since 0.9.0), with DL models via DeLFT/TensorFlow 2.17. Distributed as Docker images (rootless and ARM64 builds); Windows is not mentioned. — [GROBID releases](https://github.com/kermitt2/grobid/releases)
- **PyMuPDF-Layout:** marketed as "10× faster PDF parsing without GPUs" (vendor claim). — [Artifex blog](https://artifex.com/blog/pymupdf-layout-10-faster-pdf-parsing-without-gpus)
- **Docling speed (vendor benchmark):** 2.1 pages/s against MinerU 2.5-Pro at 0.54 pages/s on Datalab's hardware. — [Marker GitHub](https://github.com/datalab-to/marker)

### Inferences
- With 6 GB VRAM and one model loaded at a time, the 0.26–1.2B models (granite-docling, PaddleOCR-VL, MinerU2.5/Pro) should fit. 7B olmOCR does not. MinerU's ONNX GPU threshold of "≥6 GiB dedicated" means a 6 GB laptop card (minus Windows desktop overhead) may fall back to CPU, so test it.
- Python 3.14 + torch 2.14 + cu130 is the riskiest constraint. Only MinerU states 3.14 support. Docling (ONNX/torch models) and Marker give only a "≥3.10" floor. PaddleOCR-VL depends on the Paddle framework rather than PyTorch, and its Windows path is WSL or Docker (an inference from the Windows guidance; Paddle availability for Python 3.14 was not verified). Plan a fallback venv (for example Python 3.12) if a tool's wheels lag.
- GROBID without WSL: Docker Desktop on Windows normally uses a WSL2 backend (general knowledge, not verified here). A native Java run on Windows is not documented in the sources read, so GROBID may conflict with the "no WSL" constraint.
- Since throughput matters less, MinerU2.5-Pro's lower speed (0.54 pages/s on vendor hardware, likely much slower on a laptop RTX 3060) is acceptable for offline batches.

### Gaps
- No measured pages per minute for any tool on a 6 GB Ampere laptop GPU or on a Ryzen 5 5600H CPU.
- No confirmed peak VRAM per MinerU 4.x backend (pipeline, VLM, hybrid).
- No confirmation for any tool of compatibility with torch 2.14 / CUDA 13.0 specifically.
- RAM needs (16 GB system) were not documented for any tool.

## Q5. Output format suited to chunking (Markdown/JSON with structure, page and section anchors)

### Takeaway
Docling has the richest structured output: a lossless DoclingDocument JSON from which Markdown, HTML and DocTags are exported, with a built-in chunker per its docs. MinerU, Marker and PyMuPDF4LLM produce Markdown plus JSON. GROBID produces TEI-XML, which is ideal for metadata and references.

### Cited Findings
- **Docling:** exports Markdown, HTML, WebVTT, DocLang, DocTags and lossless JSON, all built on a unified DoclingDocument representation. — [Docling GitHub](https://github.com/docling-project/docling)
- **Marker:** outputs Markdown, JSON, HTML and "chunks", each with a metadata dictionary. — [Marker GitHub](https://github.com/datalab-to/marker)
- **GROBID:** TEI-XML output, with URL identification and footnote-callout linking. — [GROBID releases](https://github.com/kermitt2/grobid/releases)

### Inferences
- For citation anchors (page plus section), Docling's JSON and MinerU's middle/content JSON (block-level page indices; not verified in this pass) are preferable to plain Markdown.
- Join GROBID TEI references with the parser's body text by page or offset, so that the reference block is stripped from chunks and stored as metadata.

### Gaps
- Docling HybridChunker details and the page-provenance format were not confirmed in this pass (the fetched README did not cover them).
- MinerU's JSON schema (bounding boxes, page_idx, block types for references, headers and footers) was not verified from primary docs in this pass.

## Q6. License for a public open-source repository

### Takeaway
The permissive options are Docling (MIT; Granite-Docling Apache 2.0), olmOCR (Apache 2.0) and GROBID (Apache 2.0 headers). MinerU moved from AGPLv3 to a custom "MinerU Open Source License" based on Apache 2.0 in 3.1.0; read its extra terms before use. PyMuPDF and PyMuPDF4LLM are AGPL-3.0 with a commercial alternative. Marker's code is Apache 2.0, but its weights use a modified OpenRAIL-M licence restricting commercial use above a $5M funding or revenue threshold.

### Cited Findings
- **Docling:** code MIT; model licences are separate and follow the original model packages. — [Docling GitHub](https://github.com/docling-project/docling)
- **Granite-Docling-258M:** Apache 2.0. — [HF model card](https://huggingface.co/ibm-granite/granite-docling-258M)
- **MinerU:** 3.1.0 replaced AGPLv3 with the "MinerU Open Source License" (based on Apache 2.0). 3.0.0 removed two AGPLv3 models and one CC-BY-NC-SA 4.0 model (layoutreader). — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog)
- **Marker:** code Apache 2.0. Weights under a modified AI Pubs Open RAIL-M licence: free for research, personal use and startups under $5M funding or revenue; larger commercial use needs a paid licence. — [Marker GitHub](https://github.com/datalab-to/marker)
- **olmOCR:** Apache 2.0. — [olmOCR GitHub](https://github.com/allenai/olmocr)
- **PyMuPDF4LLM:** inherits PyMuPDF's AGPL-3.0, with a commercial licence from Artifex. The PyPI page describes `pymupdf-layout` as a "commercial extension". — [file2markdown guide (secondary)](https://www.file2markdown.ai/blog/pymupdf4llm-what-it-is); [pymupdf-layout on PyPI](https://pypi.org/project/pymupdf-layout/)
- **GROBID:** 0.9.1 added Apache 2.0 licence headers to its source files. — [GROBID releases](https://github.com/kermitt2/grobid/releases)
- **PaddleOCR-VL:** licence not confirmed in this pass. A mirror's model card front matter has a license field, but its value was not read. — [PaddleOCR-VL mirror](https://gitserver.onethingai.com/ai-models/PaddleOCR-VL/src/branch/pr/junesgone/20251017203326)

### Inferences (ranked recommendation for this hardware and project)
1. **Primary PDF parser: MinerU 4.x (hybrid or VLM backend with MinerU2.5-Pro, `effort=high`).** Second-best open score on OmniDocBench v1.6 (95.75) with strong reading order (0.120). Python 3.14 support, native Windows GPU via lmdeploy, DOCX/EPUB/HTML support, PP-OCR Cyrillic, and a no-longer-AGPL licence. Risk: the ≥6 GiB ONNX threshold on a 6 GB laptop card, and the custom licence text.
2. **References and bibliographic metadata: GROBID 0.9.1 alongside the main parser.** Still the only purpose-built reference parser, with CrossRef or biblio-glutton DOI consolidation; the March 2026 benchmark supports GROBID for clean PDFs, with an LLM fallback for hard cases. Risk: Docker/Java on Windows without WSL.
3. **Format-wide framework and fallback: Docling (MIT).** Best licence and format coverage, active maintenance, structured JSON, pluggable VLM presets, and the granite-docling 258M model fits easily. Weaker accuracy evidence (no neutral OmniDocBench row; 67.5 against MinerU's 87.1 on Datalab's vendor benchmark).
4. **Accuracy alternative: PaddleOCR-VL-1.6 (0.9B, OmniDocBench v1.6 96.34).** Highest score and wide language coverage, but Windows-native and Python 3.14 support are doubtful (WSL or Docker advised) and the licence is unverified. Arguably easiest to reach through a toolkit that wraps it rather than directly.
5. **CPU-only lightweight option: PyMuPDF4LLM 1.28 with Layout.** No GPU needed and big layout gains in 2026, but AGPL-3.0 forces the repository to be AGPL-compatible, and there are no OmniDocBench numbers.
- **Not recommended:** olmOCR (≥12 GB VRAM); Marker (weights licence restrictions and lowest OmniDocBench score among the tools listed: 78.44 on v1.6, 71.30 on v1.5).

### Gaps
- The full text and additional conditions of the "MinerU Open Source License" were not read.
- PaddleOCR-VL licence (model weights) not verified.
- `pymupdf-layout` licence terms not verified ("commercial extension" wording).
- Licence of the OCR models Docling uses by default (for example RapidOCR models) not checked.
