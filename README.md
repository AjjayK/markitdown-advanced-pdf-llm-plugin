# markitdown-advanced-pdf-llm-plugin

## Overview
markitdown-advanced-pdf-llm-plugin is a plugin for the [MarkItDown](https://github.com/microsoft/markitdown) library, specifically engineered for extracting the knowledge out of complex multi-modal PDF documents which is non-text heavy. This plugin addresses the challenges of reduced LLM output quality on large multi-modal documents by leveraging higher intelligence Large Language Models (LLMs) to interpret/extract knowledge out of these documents.

## Why MarkItDown
MarkItDown is a lightweight Python utility for converting various files to Markdown for use with LLMs and related text analysis pipelines. Markdown is extremely close to plain text, with minimal markup or formatting, but still provides a way to represent important document structure. Mainstream LLMs, such as OpenAI's GPT-4o, natively "speak" Markdown, and often incorporate Markdown into their responses unprompted. This suggests that they have been trained on vast amounts of Markdown-formatted text, and understand it well. As a side benefit, Markdown conventions are also highly token-efficient.

## Why markitdown-advanced-pdf-llm-plugin
- Token efficiency: When involving Multi-Modal document in RAG, text only capabilities consume less token than multi-modal capabilities
- RAG output quality: The quality of LLMs output degrades as input token increases. Passing several pages of multi-modal document at once can lead to poor LLM summarization than several pages of text documents 
- Latency: Text only input has lesser latency than multi-modal input

### Example page from a document where plugin is beneficial
![Screenshot 2025-05-04 184336](https://github.com/user-attachments/assets/080d24fd-a849-475a-919d-f28eba498dbe)
