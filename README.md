# markitdown-advanced-pdf-llm-plugin

## Overview
markitdown-advanced-pdf-llm-plugin is a plugin for the [MarkItDown](https://github.com/microsoft/markitdown) library, specifically engineered for extracting the knowledge out of complex multi-modal PDF documents which is non-text heavy. This plugin addresses the challenges of reduced LLM output quality on large multi-modal documents by leveraging higher intelligence Large Language Models (LLMs) to interpret/extract knowledge out of these documents.

## Why MarkItDown
MarkItDown is a lightweight Python utility for converting various files to Markdown for use with LLMs and related text analysis pipelines. Markdown is extremely close to plain text, with minimal markup or formatting, but still provides a way to represent important document structure. Mainstream LLMs, such as OpenAI's GPT-4o, natively "speak" Markdown, and often incorporate Markdown into their responses unprompted. This suggests that they have been trained on vast amounts of Markdown-formatted text, and understand it well. As a side benefit, Markdown conventions are also highly token-efficient.

## Why markitdown-advanced-pdf-llm-plugin
- Token efficiency: When involving Multi-Modal document in RAG, text only capabilities consume less token than multi-modal capabilities
- RAG output quality: The quality of LLMs output degrades as input token increases. Passing several pages of multi-modal document at once can lead to poor LLM summarization than several pages of text documents 
- Latency: Text only input has lesser latency than multi-modal input

## What it does?
### SimpleLLMKnowledgeExtractor
- Converts each PDF page to both a standalone PDF and an image
- prompts LLM (presently only OpenAI Client) to extract all text, tables, and picture information
- Processes pages concurrently for improved performance
- Generates a complete markdown document with both extracted content and adds page image

### Future Extractor (In Progress)
Current approach of sending full pages to LLMs sometimes results in incomplete extraction or information loss. Future extractor's goal is to 
- Make the extraction more deterministic by extracting each element (text, table and picture) using libraries like PyMuPDF4LLM
- Validate the deterministic extraction performed well using LLM
- Apply LLM extraction if needed

### Example page from a document where this plugin is beneficial
![Screenshot 2025-05-04 184336](https://github.com/user-attachments/assets/080d24fd-a849-475a-919d-f28eba498dbe)

## Installation
The plugin is available for installation through pip

```
pip install markitdown-advanced-pdf-llm-plugin
```

## Usage
```
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI(api_key="openai-key")

md = MarkItDown(enable_plugins=True, llm_client=openai_client, llm_model="prefered-model") # Incase custom prompt, use arg 'llm_prompt'
result = md.convert("doc.pdf")

markdown_content = result.markdown
```
