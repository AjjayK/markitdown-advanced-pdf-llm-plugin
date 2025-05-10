import sys
import io
from typing import BinaryIO, Any, Union
import fitz  # PyMuPDF
from PIL import Image
import base64

import concurrent.futures
from markitdown import (
    MarkItDown,
    DocumentConverter,
    DocumentConverterResult,
    StreamInfo
)


__plugin_interface_version__ = (
    1
)

MISSING_DEPENDENCY_MESSAGE = """
{converter} recognized the input as a potential {extension} file, but the dependencies needed to read {extension} files have not been installed.

To resolve this error, include the dependency
    pip install pypdf
"""

_dependency_exc_info = None
try:
    import pypdf
except ImportError:
    _dependency_exc_info = sys.exc_info()

ACCEPTED_MIME_TYPE_PREFIXES = [
    "application/pdf",
    "application/x-pdf",
]

ACCEPTED_FILE_EXTENSIONS = [".pdf"]


def register_converters(markitdown: MarkItDown, **kwargs):
    """
    Called during construction of MarkItDown instances to register converters provided by plugins.
    """

    # Simply create and attach an RtfConverter instance
    markitdown.register_converter(SimpleLLMKnowledgeExtractor(), priority=-1.0)

def _process_single_page(file_stream, llm_client, llm_model, llm_prompt, page_num):
    # Read the PDF
    reader = pypdf.PdfReader(io.BytesIO(file_stream))
    # Create a new PDF with just this page
    writer = pypdf.PdfWriter()
    writer.add_page(reader.pages[page_num])
    
    # Convert to base64
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    page_base64 = base64.b64encode(output_buffer.getvalue()).decode("utf-8")

    # Load the PDF from bytes
    pdf_document = fitz.open(stream=output_buffer.getvalue(), filetype="pdf")
    pdf_page = pdf_document[0]  # Get the first (and only) page
    
    # Render page to an image (adjust resolution as needed)
    pix = pdf_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for higher resolution
    
    # Convert to PIL Image and save as PNG
    img_buffer = io.BytesIO()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    
    # Get base64 of the image
    image_base64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

    # Get analysis from OpenAI
    response = llm_client.responses.create(
        model=llm_model,
        input=[
            {
                "role": "system",
                "content": [{
                    "type": "input_text",
                    "text": llm_prompt
                }]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "filename": f"page_{page_num + 1}.pdf",
                        "file_data": f"data:application/pdf;base64,{page_base64}",
                    },
                    {
                        "type": "input_text",
                        "text": "Extract",
                    },
                ],
            },
        ]
    )

    return {
        'page_number': page_num + 1,
        'extract': response.output_text,
        'base64_data': image_base64
    }

class SimpleLLMKnowledgeExtractor(DocumentConverter):
    """
    A class for building knowledge base on multi modal (Image and Text like presentation files) or image heavy documents 
    using OpenAI's API 
    
    """

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,  # Options to pass to the converter
    ) -> bool:
        
        # Only accept if LLM capabilities are available
        if not (kwargs.get("llm_client") and kwargs.get("llm_model")):
            return False

        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        for prefix in ACCEPTED_MIME_TYPE_PREFIXES:
            if mimetype.startswith(prefix):
                return True

        return False
    
    def convert(
            self,
            file_stream: BinaryIO,
            stream_info: StreamInfo,
            **kwargs: Any,
    ) -> DocumentConverterResult:
        if _dependency_exc_info is not None:
            raise ImportError(
                MISSING_DEPENDENCY_MESSAGE.format(
                    converter=type(self).__name__,
                    extension=".pdf",
                    feature="pdf",
                )
            ) from _dependency_exc_info[1]
        
        assert isinstance(file_stream, io.IOBase)

        default_prompt = '''
        You are an AI Assistant and you are an expert in extracting information from any type of document.
        Your task is to analyze this document and extract ALL useful information. You will return content only from this document and you will not add anything extra

        # Instructions
        ## Identify and Preserve All Content
        - If you find text, return the text unmodified
        - If you find a table, extract and return the table with same structure
        - If you find a chart or picture, interpret the chart or picture and describe it in clear terms.

        ## No Omissions
        - Do not leave out any relevant information from the document.
        - Ensure that every piece of data, table, or textual insight is included in your final output.

        ## Output Structure
        - Organize your extracted information in a clear, readable format.
        - DO NOT repeat anything from the given instruction or system prompt.
        - Keep only the information from the content of the given document. 
        - Only extract and DO NOT try to hallucinate anything from the provided document
        '''

        llm_client = kwargs.get("llm_client")
        llm_model = kwargs.get("llm_model")
        llm_prompt = kwargs.get("llm_prompt", default_prompt)
        max_workers = kwargs.get("max_workers", None)

        pages_data = []
        file_bytes = file_stream.read()
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        num_pages = len(reader.pages)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # process each page
            future_to_page = {
                executor.submit(
                    _process_single_page,
                    file_bytes,
                    llm_client,
                    llm_model,
                    llm_prompt,
                    page_num
                ): page_num for page_num in range(num_pages)
            }

            for future in concurrent.futures.as_completed(future_to_page):
                try:
                    page_data = future.result()
                    pages_data.append(page_data)
                except Exception as e:
                    page_num = future_to_page[future]
                    print(f"Error processing page {page_num}: {str(e)}")

        # Sort pages_data by page number to maintain order
        pages_data.sort(key=lambda x: x['page_number'])

        # Combine all pages into final markdown
        combined_text = "# Extracted Knowledge from PDF\n\n"
        for page_data in pages_data:
            combined_text += f"## Page {page_data['page_number']}\n{page_data['extract']}\n\n"
            # Add the page image in markdown format
            combined_text += f"![Page {page_data['page_number']} Image](data:image/png;base64,{page_data['base64_data']})\n\n"

        return DocumentConverterResult(
            markdown=combined_text,
        )
