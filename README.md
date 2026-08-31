# PRISM

## AI-Powered Construction Progress Intelligence

PRISM is an AI-powered construction progress document intelligence system designed to turn unstructured project reports into structured, validated construction data.

Construction progress reports often contain important information buried inside paragraphs, PDFs, and inconsistent reporting formats. PRISM processes these documents, extracts the relevant construction activities and project metadata, and converts them into structured data that can be used for monitoring, analysis, and eventually risk prediction.

The goal is simple:

> Turn construction reports into data that a project management system can actually understand.

---

## What PRISM Does

PRISM currently focuses on the document intelligence layer of construction monitoring.

A typical progress report might contain information such as:

```text
Foundation RCC work is 70 percent complete.
120 cubic meters of concrete were completed.
Heavy rainfall delayed the work by 3 hours.
The activity is currently in progress.
Instead of treating this as plain text, PRISM converts it into structured information:
{
  "activity_name": "Foundation RCC work",
  "quantity_completed": 120,
  "unit": "cubic meters",
  "progress_percentage": 70,
  "status": "In Progress",
  "issues": [
    "Heavy rainfall"
  ],
  "delay_reason": "Heavy rainfall",
  "delay_duration_hours": 3
}
This structured representation can then be consumed by downstream construction intelligence systems.
Core Pipeline
PRISM follows a hybrid extraction pipeline rather than sending everything directly to an LLM.
                 Construction Report
                         |
                         v
                  File Processing
                         |
                         v
                  PDF Extraction
                         |
                         v
             Deterministic Metadata
                  Extraction
                         |
                         v
                Gemini Semantic
                   Extraction
                         |
                         v
              Structured JSON Output
                         |
                         v
               Pydantic Validation
                         |
                         v
              Normalization / Checks
                         |
                         v
                 ProgressReport
The system deliberately separates deterministic extraction from AI-based semantic extraction.
This makes the pipeline more predictable and reduces the amount of information the model needs to infer.
Key Features
1. PDF Document Processing
PRISM can process construction progress report PDFs and extract their textual content for downstream analysis.
The PDF layer is separated from the semantic extraction layer so that document processing and AI reasoning remain independent components.
2. Deterministic Metadata Extraction
Project-level metadata is extracted separately from the AI activity extraction process.
Currently supported metadata includes:
- Project name
- Report date
- Location
- Contractor
This prevents the LLM from unnecessarily handling information that can be extracted deterministically.
3. AI-Powered Activity Extraction
Gemini is used for semantic extraction of construction activities.
PRISM can identify:
- Construction activity
- Quantity completed
- Unit
- Progress percentage
- Activity status
- Activity-specific issues
- Delay reason
- Delay duration
- General project issues
The AI output is constrained by a predefined schema instead of being treated as free-form text.
4. Strict Extraction Rules
PRISM follows a conservative extraction philosophy.
The model is explicitly instructed to:
- Extract only information present in the source
- Never invent missing information
- Never estimate missing values
- Never calculate values that were not explicitly provided
- Preserve numerical values
- Preserve the original unit wording
- Use null for unavailable information
- Extract every identifiable activity
- Avoid duplicate activity objects
This is especially important for construction data, where fabricated values could lead to incorrect project decisions.
5. Activity Association and Deduplication
Construction activities are not always described in a single sentence.
For example:
Foundation RCC work is 70 percent complete.

120 cubic meters of concrete were completed.

Heavy rainfall delayed the work by 3 hours.

The activity is currently in progress.
PRISM understands that these statements describe the same activity and combines them into a single structured activity object.
Instead of producing four fragmented records, it produces:
Foundation RCC Work
├── Progress: 70%
├── Quantity: 120 cubic meters
├── Status: In Progress
├── Issue: Heavy rainfall
├── Delay Reason: Heavy rainfall
└── Delay Duration: 3 hours
This makes the extracted data much more useful for downstream analysis.
Structured Data Models
PRISM uses Pydantic models to enforce the structure of extracted information.
The core models include:
ProgressReport
Represents the complete processed construction report.
Contains:
- Report date
- Project name
- Contractor
- Location
- Activities
- General issues
- Extraction metadata
ActivityProgress
Represents an individual construction activity.
Contains:
- Activity name
- Quantity completed
- Unit
- Progress percentage
- Status
- Issues
- Delay reason
- Delay duration
- Extraction evidence
- Extraction confidence
ExtractionEvidence
Stores text evidence associated with extracted fields.
ExtractionConfidence
Provides a structured representation for extraction confidence.
ExtractionMetadata
Stores information about the extraction process itself.
Validation
AI output is never blindly accepted.
The extraction pipeline follows:
Gemini Response
      |
      v
JSON Validation
      |
      v
Pydantic Model Validation
      |
      v
Progress Report Validation
      |
      v
Validated Output
This gives PRISM a validation layer between the AI model and the rest of the application.
For example:
Progress Percentage
        |
        v
0 <= value <= 100
and confidence values are constrained to:
0 <= confidence <= 1
Technology Stack
Language
- Python
AI / Machine Learning
- Google Gemini
- Google GenAI SDK
Data Validation
- Pydantic
Document Processing
- PyMuPDF
- EasyOCR where required by the document processing pipeline
Testing
- Pytest
- Mock-based AI testing
Project Architecture
The core application is organized around separate services for each responsibility.
PRISM/
│
├── app/
│   ├── core/
│   │   └── config.py
│   │
│   ├── schemas/
│   │   └── project_data.py
│   │
│   ├── services/
│   │   ├── extraction_service.py
│   │   ├── file_router.py
│   │   ├── pdf_service.py
│   │   ├── preprocessor.py
│   │   └── validation_service.py
│   │
│   └── ...
│
├── tests/
│   ├── test_gemini_extraction.py
│   ├── test_pdf_extraction.py
│   ├── test_project_schema.py
│   └── ...
│
├── requirements.txt
│
└── README.md
The exact application structure may evolve as PRISM moves into its next development phase.
Installation
Clone the repository:
git clone <your-repository-url>
cd PRISM
Create a virtual environment:
python -m venv venv
Activate it on Windows:
venv\Scripts\activate
Install dependencies:
pip install -r requirements.txt
Environment Variables
PRISM requires a Gemini API key for AI-based extraction.
Create a .env file:
GEMINI_API_KEY=your_gemini_api_key
Do not commit your API key to the repository.
Make sure .env is included in .gitignore.
Running Tests
Run the complete test suite:
python -m pytest -v
The current Phase 1 test suite covers:
- Gemini extraction logic
- PDF extraction
- Multiple construction activities
- Missing information handling
- Delay extraction
- Project metadata extraction
- Pydantic schema validation
Current status:
5 tests passed
Testing Without Burning API Quota
PRISM's regular test suite does not need to make live Gemini API calls.
The Gemini response is mocked during unit testing:
Pytest
  |
  v
Mock Gemini Response
  |
  v
ExtractionService
  |
  v
Validation
  |
  v
Assertions
This makes the test suite:
- Faster
- Deterministic
- Independent of API availability
- Independent of Gemini free-tier quotas
Live Gemini API testing can be performed separately when required.
Example
Input
Daily Progress Report

Project: Delhi Metro Extension
Date: 5 June 2025
Location: Block A

Foundation RCC work is 70 percent complete.
120 cubic meters of concrete were completed.

Heavy rainfall delayed the work by 3 hours.

The activity is currently in progress.
Output
{
  "report_date": "5 June 2025",
  "project_name": "Delhi Metro Extension",
  "location": "Block A",
  "activities": [
    {
      "activity_name": "Foundation RCC work",
      "quantity_completed": 120,
      "unit": "cubic meters",
      "progress_percentage": 70,
      "status": "In Progress",
      "issues": [
        "Heavy rainfall"
      ],
      "delay_reason": "Heavy rainfall",
      "delay_duration_hours": 3
    }
  ]
}
Design Philosophy
PRISM is built around a simple principle:
AI should extract meaning, but software should enforce correctness.

Instead of relying entirely on an LLM, PRISM combines:
Deterministic Processing
        +
Semantic AI Extraction
        +
Structured Schemas
        +
Validation
        =
Reliable Construction Data
This hybrid approach provides a stronger foundation for building higher-level construction intelligence systems.
Phase 1 — Document Intelligence Foundation
Phase 1 is complete.
Completed
- PDF ingestion
- PDF text extraction
- Project metadata extraction
- Gemini semantic extraction
- Structured JSON generation
- Pydantic schema validation
- Construction activity extraction
- Quantity and unit extraction
- Progress extraction
- Activity status extraction
- Issue extraction
- Delay reason extraction
- Delay duration extraction
- Activity association
- Activity deduplication
- Missing-information handling
- Extraction evidence structure
- Extraction confidence structure
- Automated test coverage
Current test status:
5 / 5 tests passing
Phase 2 — Construction Risk & Progress Intelligence
The next stage of PRISM is to move beyond extraction.
The goal is to allow PRISM to reason over construction progress rather than simply convert documents into structured data.
Planned capabilities include:
Progress Reports
       |
       v
Historical Project Data
       |
       v
Progress Analysis
       |
       v
Delay Detection
       |
       v
Risk Assessment
       |
       v
Schedule Impact
       |
       v
Actionable Insights
Potential future capabilities include:
- Progress trend analysis
- Delay pattern detection
- Construction risk scoring
- Schedule impact analysis
- Historical activity comparison
- Repeated issue detection
- Project health indicators
- Predictive delay analysis
- AI-generated project insights
The long-term goal is to turn PRISM from a document extraction system into a construction intelligence platform.
Why PRISM?
Construction projects generate huge amounts of documentation, but much of the useful information remains trapped inside unstructured reports.
PRISM creates a bridge between those reports and intelligent project monitoring systems.
Instead of:
PDF → Human reads → Human interprets → Spreadsheet
PRISM aims toward:
PDF
 ↓
PRISM
 ↓
Structured Construction Data
 ↓
Analysis
 ↓
Risk Intelligence
 ↓
Decision Support
Project Status
Phase 1: Document Intelligence       [██████████] Complete
Phase 2: Risk & Progress Intelligence[░░░░░░░░░░] Planned
Phase 3: Predictive Intelligence     [░░░░░░░░░░] Planned
PRISM is currently in active development.
Author
Vaibhav Mohanty
AI/ML Engineering Student
PRISM is being developed as an applied AI/ML project focused on document intelligence, structured information extraction, and intelligent construction monitoring.

One thing I'd **definitely keep** in this README is the line:

> **AI should extract meaning, but software should enforce correctness.**

That captures the technical idea behind what you've actually built and makes PRISM sound substantially more mature than *"I used Gemini to extract stuff from PDFs."*




 





Make a whole readme  and keep all this in one readme make sure nothing is left out and be a little creative gpt make the readme file attractive more come on i know youve got that creativity in you













Oh, now we're making the README properly. 😭
The previous one was technically good, but it read a little too much like documentation. For a project like PRISM, the README should make someone scrolling through your GitHub think:
"Okay, this isn't just another Gemini + PDF project. This guy actually built a system."

Here’s a more polished, creative, single-file, copy-paste-ready README that keeps the technical details, Phase 1 accomplishments, architecture, testing, and future roadmap — while giving PRISM an actual identity.
# PRISM

### **Project Report Intelligence & Site Monitoring**

> **Turning construction reports into structured intelligence.**

PRISM is an AI-powered construction progress intelligence system that transforms unstructured project reports into structured, validated, machine-readable construction data.

Construction sites generate enormous amounts of information every day — progress reports, activity updates, quantities, delays, issues, contractor information, and site conditions.

The problem?

Much of that information is still trapped inside PDFs and paragraphs.

PRISM is built to change that.

Instead of making a project manager manually read through every report and extract the important information, PRISM processes the document, identifies the relevant construction activities, understands their context, validates the extracted information, and converts everything into structured data ready for analysis.

The long-term vision is bigger than document extraction.

PRISM is being built toward an intelligent construction monitoring system capable of understanding **what is happening on a project, why it is happening, and where potential risks are emerging.**

---

## The Idea

Imagine receiving a daily construction report containing something like:

```text
Foundation RCC work is 70 percent complete.
120 cubic meters of concrete were completed.

Heavy rainfall delayed the work by 3 hours.

The activity is currently in progress.
To a human, this is easy to understand.
To a software system, it is just a block of text.
PRISM bridges that gap.
It converts the report into structured information:
{
  "activity_name": "Foundation RCC work",
  "quantity_completed": 120,
  "unit": "cubic meters",
  "progress_percentage": 70,
  "status": "In Progress",
  "issues": [
    "Heavy rainfall"
  ],
  "delay_reason": "Heavy rainfall",
  "delay_duration_hours": 3
}
Now that information can be stored, compared, visualized, analyzed, and eventually used for intelligent decision-making.
That is the core idea behind PRISM.
Why PRISM?
Construction progress monitoring often follows a workflow like this:
PDF Report
    ↓
Human reads report
    ↓
Human identifies useful information
    ↓
Human interprets progress
    ↓
Human updates spreadsheet/system
    ↓
Management reviews data
PRISM aims to move toward:
                 PDF Report
                     │
                     ▼
              ┌─────────────┐
              │    PRISM    │
              └──────┬──────┘
                     │
                     ▼
           Structured Construction Data
                     │
                     ▼
             Progress Intelligence
                     │
                     ▼
              Risk Detection
                     │
                     ▼
             Decision Support
The goal isn't simply to replace a spreadsheet.
The goal is to build the intelligence layer between construction documentation and project decision-making.
Current Status
Phase 1 — Document Intelligence Foundation
Status: COMPLETE
██████████████████████████████  100%
The complete Phase 1 test suite currently passes:
5 / 5 tests passing
Phase 1 establishes the foundation required for the future intelligence layers.
What PRISM Can Do Today
Document Processing
PRISM can process construction progress report PDFs and extract their textual content for further analysis.
Metadata Extraction
Project-level information is extracted separately from semantic activity extraction.
Currently supported:
- Project name
- Report date
- Location
- Contractor
Construction Activity Extraction
PRISM can identify individual construction activities and extract:
- Activity name
- Quantity completed
- Unit
- Progress percentage
- Activity status
- Activity-specific issues
- Delay reason
- Delay duration
- General project issues
Missing Information Handling
PRISM follows a strict rule:
If the document doesn't say it, PRISM doesn't make it up.

Missing information is represented using null rather than guessed values.
For example:
{
  "activity_name": "Earthwork excavation",
  "quantity_completed": 350,
  "unit": "cubic meters",
  "progress_percentage": null,
  "status": "In Progress",
  "issues": [],
  "delay_reason": null,
  "delay_duration_hours": null
}
No invented progress percentage.
No estimated delay.
No fabricated information.
The Extraction Philosophy
PRISM uses a conservative extraction approach.
The AI is explicitly instructed to:
- Extract only information explicitly present in the source
- Never invent information
- Never estimate missing values
- Never calculate missing values
- Preserve numerical values exactly
- Preserve original unit wording
- Preserve explicit progress percentages
- Preserve explicit delay durations
- Use null when information is unavailable
- Extract every identifiable construction activity
- Avoid duplicate activities
- Avoid commentary in structured output
This matters because construction data isn't the place for creative hallucinations.
A model saying:
"The project is probably around 80% complete."

might sound intelligent.
In a construction monitoring system, it's simply wrong.
Activity Association
One of the important problems PRISM handles is that information about the same activity can be spread across multiple sentences.
For example:
Foundation RCC work is 70 percent complete.

120 cubic meters of concrete were completed.

Heavy rainfall delayed the work by 3 hours.

The activity is currently in progress.
A naive extraction system might produce several fragmented objects.
PRISM instead associates these statements with the same construction activity.
Foundation RCC Work
│
├── Progress
│   └── 70%
│
├── Quantity
│   └── 120 cubic meters
│
├── Status
│   └── In Progress
│
├── Issue
│   └── Heavy rainfall
│
├── Delay Reason
│   └── Heavy rainfall
│
└── Delay Duration
    └── 3 hours
The result is one coherent activity object.
Deduplication
PRISM also prevents duplicate activity objects.
If multiple sentences refer to the same activity, their information is merged rather than producing multiple records.
"Foundation RCC work is 70% complete."

"120 cubic meters of concrete were completed."

"The foundation work remains in progress."
Becomes:
Foundation RCC Work
rather than:
Foundation RCC Work
Foundation RCC Work
Foundation Work
This is important when the extracted data is later used for analytics or historical comparisons.
Hybrid AI Architecture
PRISM intentionally does not send every extraction task to the LLM.
Instead, it follows a hybrid approach:
             SOURCE DOCUMENT
                    │
                    ▼
          ┌───────────────────┐
          │ PDF / File Router │
          └─────────┬─────────┘
                    │
                    ▼
          ┌───────────────────┐
          │ Text Extraction   │
          └─────────┬─────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   Deterministic         Semantic
    Processing           Processing
          │                   │
          │                   ▼
          │             Gemini AI
          │                   │
          └─────────┬─────────┘
                    │
                    ▼
             Structured JSON
                    │
                    ▼
          ┌───────────────────┐
          │ Pydantic Models   │
          └─────────┬─────────┘
                    │
                    ▼
          Validation & Normalization
                    │
                    ▼
             ProgressReport
This separation gives PRISM a much stronger foundation than relying entirely on free-form LLM output.
Why Hybrid Processing?
Some information is deterministic.
For example:
Project: Delhi Metro Extension
Date: 5 June 2025
Location: Block A
There is little reason to ask an LLM to "reason" about this.
Other information is semantic.
For example:
Heavy rainfall caused a three-hour interruption
to foundation RCC operations.
Understanding that:
issue = Heavy rainfall
delay_reason = Heavy rainfall
delay_duration = 3 hours
requires contextual understanding.
PRISM therefore uses:
Deterministic logic
        +
Semantic AI
        +
Schema validation
        =
Reliable structured information
Structured Data Layer
PRISM uses Pydantic models to create a strict contract between the AI layer and the rest of the application.
The core models include:
ProgressReport
Represents the complete construction report.
Contains:
- Report date
- Project name
- Contractor
- Location
- Activities
- General issues
- Extraction metadata
ActivityProgress
Represents a single construction activity.
Contains:
- Activity name
- Quantity completed
- Unit
- Progress percentage
- Status
- Issues
- Delay reason
- Delay duration
- Extraction evidence
- Extraction confidence
ExtractionEvidence
Stores supporting text associated with extracted activity information.
Supported evidence categories include:
progress
quantity
status
delay
This creates a foundation for traceable AI extraction.
ExtractionConfidence
Provides a structured representation for extraction confidence.
Confidence values are constrained between:
0.0 ─────────────── 1.0
ExtractionMetadata
Stores information about the extraction process, including:
- Source type
- Processing method
- Confidence score
Validation Layer
PRISM doesn't blindly trust AI output.
The validation pipeline is:
Gemini
   │
   ▼
JSON Response
   │
   ▼
AIActivityExtraction
   │
   ▼
Pydantic Validation
   │
   ▼
ProgressReport
   │
   ▼
Progress Report Validation
   │
   ▼
Validated Output
For example:
Progress percentage
0 <= progress_percentage <= 100
Confidence
0 <= confidence <= 1
Missing values
Missing information → null
This provides a software-enforced boundary around the AI layer.
AI Output Contract
Gemini is instructed to return structured JSON matching the application schema.
The model isn't asked to produce:
"Here's what I found..."
It is asked to produce machine-readable structured data.
Conceptually:
Document
   ↓
Semantic understanding
   ↓
Structured JSON
   ↓
Schema validation
   ↓
Application data
This makes the AI component much easier to integrate with downstream services.
Testing Strategy
PRISM uses pytest for automated testing.
The current test suite covers:
PDF Extraction
test_multiple_activities_pdf
test_missing_information_pdf
test_delay_heavy_pdf
Gemini Extraction
test_gemini_extraction
Project Schema
test_progress_report
Current result:
==============================

5 passed

==============================
Why the Gemini Test Is Mocked
A major design decision in Phase 1 was separating unit testing from live API testing.
A normal test run should not depend on:
- Gemini availability
- Internet connectivity
- API quota
- API latency
- Billing limits
Therefore, the Gemini response is mocked during the unit test.
                 PYTEST
                    │
                    ▼
             Mock Gemini
                    │
                    ▼
           ExtractionService
                    │
                    ▼
              Validation
                    │
                    ▼
                Assertions
This means the normal test suite can run repeatedly without consuming Gemini API quota.
Live Gemini calls can be tested independently when required.
Example
Input
Daily Progress Report

Project: Delhi Metro Extension
Date: 5 June 2025
Location: Block A

Foundation RCC work is 70 percent complete.
120 cubic meters of concrete were completed.

Heavy rainfall delayed the work by 3 hours.

The activity is currently in progress.
PRISM Output
{
  "report_date": "5 June 2025",
  "project_name": "Delhi Metro Extension",
  "contractor": null,
  "location": "Block A",
  "activities": [
    {
      "activity_name": "Foundation RCC work",
      "quantity_completed": 120,
      "unit": "cubic meters",
      "progress_percentage": 70,
      "status": "In Progress",
      "issues": [
        "Heavy rainfall"
      ],
      "delay_reason": "Heavy rainfall",
      "delay_duration_hours": 3
    }
  ],
  "general_issues": []
}
Project Architecture
The current architecture is organized around separate responsibilities:
PRISM/
│
├── app/
│   │
│   ├── core/
│   │   └── config.py
│   │
│   ├── schemas/
│   │   └── project_data.py
│   │
│   ├── services/
│   │   ├── extraction_service.py
│   │   ├── file_router.py
│   │   ├── pdf_service.py
│   │   ├── preprocessor.py
│   │   └── validation_service.py
│   │
│   └── ...
│
├── tests/
│   ├── test_gemini_extraction.py
│   ├── test_pdf_extraction.py
│   ├── test_project_schema.py
│   └── ...
│
├── requirements.txt
│
├── .env
│
└── README.md
The architecture is intentionally modular so that future intelligence layers can be added without rewriting the document processing foundation.
Technology Stack
Layer	Technology
Language	Python
AI	Google Gemini
AI SDK	Google GenAI SDK
Data Validation	Pydantic
PDF Processing	PyMuPDF
OCR	EasyOCR
Testing	Pytest
Test Mocking	unittest.mock


Installation
Clone the repository:
git clone <your-repository-url>
cd PRISM
Create a virtual environment:
python -m venv venv
Activate it on Windows:
venv\Scripts\activate
Install dependencies:
pip install -r requirements.txt
Environment Configuration
Create a .env file in the project root:
GEMINI_API_KEY=your_gemini_api_key
Never commit your API key.
Make sure .env is included in .gitignore.
Running the Tests
Run the complete test suite:
python -m pytest -v
Expected result:
5 passed
You can also run individual test modules:
python -m pytest tests/test_pdf_extraction.py -v
python -m pytest tests/test_project_schema.py -v
python -m pytest tests/test_gemini_extraction.py -v
Engineering Principles
PRISM is being developed around a few core principles.
1. Don't hallucinate data
If the report doesn't contain it, don't invent it.
2. Separate deterministic logic from AI reasoning
Use traditional software where traditional software is better.
Use AI where semantic understanding is required.
3. Validate AI output
AI-generated data should pass through strict application-level validation.
4. Preserve evidence
Extracted information should eventually be traceable back to the source document.
5. Build for downstream intelligence
The extraction layer isn't the final product.
It is the foundation for analysis, prediction, and decision support.
Phase 1: Completed
PRISM's first phase focused on building a reliable document intelligence foundation.
Completed
- PDF ingestion
- PDF text extraction
- Document preprocessing
- Deterministic metadata extraction
- Project name extraction
- Report date extraction
- Location extraction
- Contractor extraction
- Gemini semantic extraction
- Structured JSON generation
- Pydantic schema validation
- Progress report validation
- Construction activity extraction
- Quantity extraction
- Unit extraction
- Progress percentage extraction
- Activity status extraction
- Issue extraction
- Delay reason extraction
- Delay duration extraction
- General issue extraction
- Missing-information handling
- Activity association across multiple sentences
- Activity deduplication
- Extraction evidence structure
- Extraction confidence structure
- Gemini response mocking
- Automated testing
- Full Phase 1 test suite passing
Phase 1 Test Status
╔══════════════════════════════════╗
║        PRISM TEST SUITE          ║
╠══════════════════════════════════╣
║                                  ║
║   Tests Run:       5             ║
║   Passed:          5             ║
║   Failed:          0             ║
║                                  ║
║   STATUS:       PASS              ║
║                                  ║
╚══════════════════════════════════╝
Phase 2: Construction Risk & Progress Intelligence
Phase 1 answers:
"What does the report say?"

Phase 2 will begin answering:
"What does it mean for the project?"

The next stage of PRISM will introduce intelligence over the structured construction data.
The planned architecture looks like:
                Progress Reports
                       │
                       ▼
                  PRISM Core
                       │
                       ▼
              Structured Data
                       │
                       ▼
             Historical Records
                       │
                       ▼
              Progress Analysis
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        Delay Detection      Trend Analysis
             │                   │
             └─────────┬─────────┘
                       ▼
                 Risk Scoring
                       │
                       ▼
               Schedule Impact
                       │
                       ▼
              Actionable Insights
Potential capabilities include:
- Progress trend analysis
- Historical activity comparison
- Delay pattern detection
- Repeated issue detection
- Construction risk scoring
- Schedule impact analysis
- Project health indicators
- Early warning signals
- Predictive delay analysis
- AI-generated project insights
The objective is to move from:
Document Extraction
to:
Construction Intelligence
Long-Term Vision
PRISM is ultimately intended to become more than a document parser.
The long-term vision is a system that can continuously understand construction project activity.
Imagine a project where PRISM receives progress reports over time:
Day 01
Foundation → 35%

Day 07
Foundation → 48%

Day 14
Foundation → 57%
Weather delays detected

Day 21
Foundation → 61%
Repeated weather delays

        ↓

PRISM identifies a pattern

        ↓

"Foundation progress is trending below
expected completion velocity."
That is where the project becomes genuinely interesting.
The system can eventually move from:
Reading reports
to:
Understanding project behavior.
The Bigger Picture
PRISM is built around a simple idea:
AI should extract meaning. Software should enforce correctness. Intelligence should drive decisions.

The document extraction layer is only the beginning.
The end goal is a system capable of connecting:
                 DOCUMENTS
                     │
                     ▼
                EXTRACTION
                     │
                     ▼
               STRUCTURED DATA
                     │
                     ▼
                 ANALYSIS
                     │
                     ▼
               RISK DETECTION
                     │
                     ▼
                PREDICTION
                     │
                     ▼
             DECISION SUPPORT
A construction report shouldn't just sit inside a folder after someone reads it.
It should become data.
That data should become insight.
And that insight should eventually help people make better decisions on the project.
Project Status
PRISM DEVELOPMENT ROADMAP

Phase 1
Document Intelligence
██████████████████████████████  COMPLETE

Phase 2
Risk & Progress Intelligence
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  NEXT

Phase 3
Predictive Construction Intelligence
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  PLANNED
PRISM is currently under active development.
Author
Vaibhav Mohanty
AI/ML Engineering Student
Interested in building systems where machine learning isn't just a model sitting inside a notebook, but part of an actual software pipeline.
PRISM is an ongoing exploration of:
- Artificial Intelligence
- Machine Learning
- LLM-based information extraction
- Document intelligence
- Structured data processing
- Construction technology
- Predictive analytics
- AI-assisted decision support
Final Thought
Construction projects produce data everywhere.
Reports.
Tables.
PDFs.
Site updates.
Delays.
Quantities.
Issues.
Progress percentages.
The challenge isn't generating more data.
The challenge is understanding the data that already exists.
That's what PRISM is being built to do.
          RAW CONSTRUCTION REPORT
                    │
                    ▼
                  PRISM
                    │
                    ▼
          STRUCTURED INFORMATION
                    │
                    ▼
               INTELLIGENCE
                    │
                    ▼
              BETTER DECISIONS
PRISM — Project Report Intelligence & Site Monitoring
From reports to intelligence.
