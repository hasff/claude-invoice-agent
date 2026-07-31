# claude-invoice-agent

[![Sponsor hasff](https://img.shields.io/badge/Sponsor-hasff-brightgreen?logo=github-sponsors)](https://github.com/sponsors/hasff)
[![Portfolio](https://img.shields.io/badge/Portfolio-AI%2FML%20Projects-blue?logo=github)](https://hasff.github.io/my-ai-portfolio/)

Extract client data from PDF invoices — name, address, phone, amount owed — and export everything to a formatted Excel file. Automatically. Powered by the Claude API and Tool Use.

*Status: May 2026*

[![Watch the demo](https://img.youtube.com/vi/xqYbqiP4QkE/maxresdefault.jpg)](https://youtu.be/xqYbqiP4QkE)

---

#### ⚡ Quick Navigation: [The Problem](#the-problem) | [How it Works](#how-it-works) | [The Agentic Loop](#the-agentic-loop) | [Output](#output) | [Quick Start](#quick-start) | [📩 Get in Touch](#need-this-for-your-organisation)

---

## The Problem 

A folder of PDF invoices. Each one formatted slightly differently. Someone needs the client data — name, address, phone number, amount owed — in a spreadsheet.

The obvious move is to open each PDF, read it, and copy the values into Excel. Except there are thirty of them. Or three hundred. And the layout changes from supplier to supplier.

So someone does it manually. Or writes a fragile script that breaks the moment a field moves.

This project solves that problem properly — using Claude as the reasoning engine, not just a text extractor.

---

## How it Works

The project has two layers: a **chat loop** that keeps the conversation with Claude, and a **tool layer** that gives Claude the ability to act on the file system.

```
main.py
    │
    ├── chat()               — main loop, manages message history
    ├── send_to_claude()     — sends messages + tools to the API
    └── process_tool_calls() — executes tools and returns results to Claude

tools.py
    │
    ├── list_pdfs()          — lists all PDFs in the invoices/ folder
    ├── extract_pdf_text()   — extracts first and last 30 lines from a PDF
    ├── create_excel()       — writes extracted data to a formatted .xlsx file
    └── read_project_code()  — lets Claude read its own source code (/explain command)
```

### Tool Definitions

Tools are defined as JSON schemas and sent to the Claude API on every request. Claude decides which tool to call, with which arguments, based on the task at hand.

```python
{
    "name": "extract_pdf_text",
    "description": "Extracts the first 30 and last 30 lines of text from a PDF file...",
    "input_schema": {
        "type": "object",
        "properties": {
            "filename": { "type": "string" }
        },
        "required": ["filename"]
    }
}
```

### PDF Extraction Strategy

Rather than extracting the full text of every page — which can be large and expensive — the extractor takes the first 30 and last 30 non-empty lines. Invoice headers (client name, address, date) sit at the top. Totals and payment details sit at the bottom. This covers most invoice formats efficiently.

```python
if len(all_lines) <= 60:
    final_content = all_lines
else:
    header = all_lines[:30]
    footer = all_lines[-30:]
    final_content = header + ["--- [Content Truncated] ---"] + footer
```

---

## The Agentic Loop

This is the core of the project. Claude does not just answer — it acts in a loop until the task is complete.

```
User: "extract client data from the invoices"
        │
        ▼
Claude calls list_pdfs()
        │
        ▼
Claude calls extract_pdf_text() for each file
        │
        ▼
Claude analyses the text, extracts fields
        │
        ▼
Claude calls create_excel() with all accumulated data
        │
        ▼
Claude confirms completion to the user
```

The loop runs inside `process_tool_calls()`. Every tool result — including errors — is returned to Claude as a message. Claude decides what to do next. If a file is missing or unreadable, Claude handles it gracefully rather than stopping.

```python
while response.stop_reason == "tool_use":
    # execute tools
    # append results to message history
    # call Claude again
    response = send_to_claude(messages)
```

---

## Output

A single Excel file saved to the `output/` folder, timestamped:

```
output/
└── clients_20260517_143022.xlsx
```

| Name | Address | Phone | Amount Owed |
|---|---|---|---|
| Acme Corp | 123 Main St, New York | +1 212 555 0100 | 4750.00 |
| Bright Solutions | 88 King Road, London | +44 20 7946 0301 | 1200.00 |

Headers are formatted with a blue background and white bold text. Column widths are auto-fitted to content.

---

## Quick Start

```bash
git clone https://github.com/hasff/claude-invoice-agent.git
cd claude-invoice-agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the root folder:

```
ANTHROPIC_API_KEY=your_api_key_here
PDFS_FOLDER=invoices
OUTPUT_FOLDER=output
```

Place your PDF invoices in the `invoices/` folder and run:

```bash
python main.py
```

Then type:

```
extract client data from the invoices
```

The agent will process all PDFs and save the result to `output/`.

### /explain command

The agent can explain its own code. Type `/explain how does the agentic loop work` and Claude will read the source files and answer based on the actual implementation.

---

## Need this for your organisation?

Invoice processing is a recurring bottleneck — finance teams, legal departments, procurement. The data is all there, locked in PDFs that don't connect to anything.

I build document extraction and automation pipelines for:

- finance and accounting teams processing supplier invoices at scale
- legal and operations teams handling structured document workflows
- anyone currently copying data out of PDFs by hand

📩 Contact: hugoferro.business(at)gmail.com

🌐 Courses and professional tools: https://hasff.github.io/site/

🔗 LinkedIn: https://www.linkedin.com/in/hugo-ferro-1434b414/

🗂️ **Portfolio:** [more AI/ML projects like this one](https://hasff.github.io/my-ai-portfolio/)