# GPT-4o Vision Prompt Templates

This directory contains example prompt templates for customizing how GPT-4o Vision extracts text from handwritten PDF images.

## Usage

### Option 1: Environment Variable
Set the prompt template directly in your `.env` file:
```bash
GPT4V_PROMPT_TEMPLATE=Your custom prompt here. Use \n for newlines.
```

### Option 2: Template File
1. Create a custom prompt template file (e.g., `my_template.txt`)
2. Set the file path in your `.env`:
```bash
GPT4V_PROMPT_TEMPLATE_FILE=./prompt_templates/my_template.txt
```

### Option 3: API Request
When uploading a PDF via the API, you can include a custom prompt template:
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@note.pdf" \
  -F "prompt_template=Your custom prompt here"
```

## Example Template

The `example.txt` file contains a default template that:
- Instructs GPT-4o to extract ALL text
- Preserves exact formatting, spelling, and structure
- Transcribes word-for-word without interpretation

## Customization Tips

When creating your own template, consider:
- **Specificity**: Be clear about what you want extracted
- **Format**: Specify how to preserve line breaks, spacing, etc.
- **Context**: Mention any domain-specific terminology or formatting requirements
- **Instructions**: Add any special handling requirements (e.g., ignore certain elements)

Example custom template for meeting notes:
```
You are an expert at transcribing meeting notes. Extract all text from this handwritten meeting note. 
Focus on preserving:
- Attendee names and titles
- Action items with clear formatting (use "  -  " for bullets)
- Dates and times in their original format
- Key decisions and discussion points

Maintain the original structure with sections separated by blank lines.
```



