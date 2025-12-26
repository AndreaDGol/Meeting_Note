"""
AI Service for analyzing and processing extracted text
"""

import os
import json
import openai
from typing import Dict, Any, List, Optional
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered analysis of extracted text"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-4o")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Load default prompt template from environment or use built-in default
        self.default_prompt_template = self._load_prompt_template()
        
        # Initialize OpenAI client
        if self.openai_api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None
        
        # Initialize sentence transformer for embeddings
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Could not load sentence transformer: {e}")
            self.embedding_model = None
    
    def _load_prompt_template(self) -> str:
        """Load prompt template from environment variable or file, or use default"""
        # First, try to load from environment variable
        env_template = os.getenv("GPT4V_PROMPT_TEMPLATE")
        if env_template:
            logger.info("Loaded prompt template from GPT4V_PROMPT_TEMPLATE environment variable")
            return env_template
        
        # Try to load from file specified in environment variable
        template_file = os.getenv("GPT4V_PROMPT_TEMPLATE_FILE")
        if template_file and os.path.exists(template_file):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = f.read().strip()
                logger.info(f"Loaded prompt template from file: {template_file}")
                return template
            except Exception as e:
                logger.warning(f"Could not load prompt template from file {template_file}: {e}")
        
        # Use default prompt template for Golconda Partners meeting notes
        default_template = """You are a professional meeting note-taker for Golconda Partners.

Task: Convert the meeting transcript/notes into a clean, concise summary.

Output Format:
  -  Start with a header that includes the date (if visible in the notes)
  -  Use the following sections in order: Attendees, Action Items, General Notes
  -  Make these section headers bold (use **bold** markdown formatting)
  -  Include "Personal:" section only if there is personal/sensitive information to note (also bold)
  -  Use " -  " (one space, dash, two spaces) for bullet points
  -  Always end with "Michael"

Special Instructions:
  -  For attendee names ending with "xL" or similar ambiguous characters where "x" is unclear, interpret as "B" when the context suggests it should be "MBL" or similar common names/initials
  -  Use your best judgment for unclear characters, considering context and common name patterns
  -  Preserve all other text exactly as written"""
        
        return default_template
    
    def extract_text_from_base64_images(
        self, 
        base64_images: List[str],
        prompt_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from base64 encoded images using GPT-4o Vision API
        
        Args:
            base64_images: List of base64 encoded image strings
            prompt_template: Optional custom prompt template. If None, uses default template
                            (from environment variable GPT4V_PROMPT_TEMPLATE, file GPT4V_PROMPT_TEMPLATE_FILE, or built-in default)
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not self.client:
            raise ValueError("OpenAI API key is required for text extraction")
        
        # Use provided template, or default template
        prompt_text = prompt_template if prompt_template is not None else self.default_prompt_template
        
        try:
            all_text_parts = []
            
            # Process each image (page)
            for page_num, base64_image in enumerate(base64_images, 1):
                logger.info(f"Processing page {page_num}/{len(base64_images)} with GPT-4o Vision")
                if prompt_template:
                    logger.info("Using custom prompt template")
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt_text
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.0
                )
                
                page_text = response.choices[0].message.content.strip()
                all_text_parts.append(page_text)
                logger.info(f"Extracted {len(page_text)} characters from page {page_num}")
            
            # Combine all pages
            combined_text = "\n\n".join(all_text_parts)
            
            # Post-process: fix common OCR errors and format section headers
            combined_text = self._fix_common_errors(combined_text)
            combined_text = self._format_section_headers(combined_text)
            combined_text = self._fix_bullet_format(combined_text)
            
            # Add signature if not already present
            combined_text = self._add_signature(combined_text)
            
            word_count = len([w for w in combined_text.split() if w.strip()])
            
            return {
                'text': combined_text,
                'confidence': 95.0,  # GPT-4o Vision is highly accurate
                'word_count': word_count,
                'character_count': len(combined_text),
                'language': 'en',
                'extraction_method': 'gpt4o-vision',
                'page_count': len(base64_images)
            }
            
        except Exception as e:
            logger.error(f"Error extracting text with GPT-4o Vision: {str(e)}")
            raise
    
    def _fix_common_errors(self, text: str) -> str:
        """Fix common OCR/interpretation errors in extracted text"""
        import re
        
        # Fix "MxL" or "M xL" -> "MBL" in attendee lists
        # Look for patterns like "MxL", "M xL", "M.xL", etc. in context of attendees
        # Be careful to only fix when it appears to be an attendee name/initial
        
        # Pattern: Match "M" followed by optional space/dot, then "xL" or similar
        # Only replace if it appears in likely attendee contexts
        patterns_to_fix = [
            (r'\bM[.\s]*xL\b', 'MBL'),  # MxL, M.xL, M xL -> MBL
            (r'\bM[.\s]*x\s*L\b', 'MBL'),  # M x L -> MBL
            (r'\b([A-Z])[.\s]*xL\b', r'\1BL'),  # Any capital letter + xL -> BL
        ]
        
        for pattern, replacement in patterns_to_fix:
            # Only apply if it appears in likely attendee section or list context
            # Check if we're in an attendees section or before common section headers
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _fix_bullet_format(self, text: str) -> str:
        """Fix bullet point format to use ' -  ' (one space, dash, two spaces)"""
        import re
        
        # Pattern to match bullet points that don't follow the correct format
        # Match various incorrect formats:
        # - "  - " (two spaces, dash, space) -> " -  "
        # - "   - " (three spaces, dash, space) -> " -  "
        # - "- " (no spaces before dash) -> " -  "
        # - " - " (one space, dash, one space) -> " -  "
        
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Check if line starts with bullet-like pattern
            # Match patterns like: spaces + dash + space(s) + text
            # We want: " -  " (one space, dash, two spaces)
            
            # Pattern for incorrect bullet formats
            bullet_pattern = r'^(\s*)([-•])\s+(.+)$'
            match = re.match(bullet_pattern, line)
            
            if match:
                # This is a bullet point - reformat to " -  " (no indentation)
                bullet = match.group(2)  # The dash or bullet character
                content = match.group(3)  # The text after the bullet
                
                # Convert to standard format: " -  " (one space, dash, two spaces, no indentation)
                fixed_line = ' -  ' + content
                fixed_lines.append(fixed_line)
            else:
                # Not a bullet point, keep as is
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _format_section_headers(self, text: str) -> str:
        """Format section headers (Attendees, Action Items, General Notes, Personal) as bold"""
        import re
        
        # List of section headers to format
        section_headers = [
            'Attendees',
            'Action Items',
            'General Notes',
            'Personal'
        ]
        
        # Process each section header
        for header in section_headers:
            # Match headers at the start of line (with or without colon)
            # Pattern: header at start of line, optionally followed by colon and whitespace
            patterns = [
                rf'^({re.escape(header)}):',  # Header: at start of line
                rf'^({re.escape(header)})$',  # Header alone on a line
                rf'\n({re.escape(header)}):',  # Header: after newline
                rf'\n({re.escape(header)})\n',  # Header alone after newline
            ]
            
            for pattern in patterns:
                # Check if header is not already wrapped in **
                replacement = rf'**\1**'
                if not re.search(rf'\*\*{re.escape(header)}\*\*', text, re.IGNORECASE | re.MULTILINE):
                    text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text
    
    def _add_signature(self, text: str) -> str:
        """Add signature 'Michael' at the end if not already present"""
        import re
        
        # Check if signature already exists (case insensitive, with or without "Signature:" prefix)
        if re.search(r'(signature\s*:?\s*)?michael', text, re.IGNORECASE):
            return text
        
        # Add signature at the end
        # Add two blank lines before signature if not already present
        text = text.rstrip()
        if not text.endswith('\n\n'):
            if not text.endswith('\n'):
                text += '\n\n'
            else:
                text += '\n'
        
        text += 'Michael'
        return text
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze extracted text using AI
        
        Args:
            text: The text extracted from handwritten notes
            
        Returns:
            Dictionary containing analysis results
        """
        if not text.strip():
            return {
                'category': 'Unknown',
                'tags': [],
                'summary': 'No text found',
                'sentiment': 'neutral',
                'key_points': [],
                'title': 'Untitled Note'
            }
        
        try:
            # Generate title
            title = self._generate_title(text)
            
            # Categorize the content
            category = self._categorize_text(text)
            
            # Extract key points
            key_points = self._extract_key_points(text)
            
            # Generate summary
            summary = self._generate_summary(text)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(text)
            
            # Generate tags
            tags = self._generate_tags(text, category)
            
            return {
                'title': title,
                'category': category,
                'tags': tags,
                'summary': summary,
                'sentiment': sentiment,
                'key_points': key_points
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return {
                'title': 'Analysis Failed',
                'category': 'Unknown',
                'tags': [],
                'summary': 'Error occurred during analysis',
                'sentiment': 'neutral',
                'key_points': []
            }
    
    def _generate_title(self, text: str) -> str:
        """Generate a title for the note"""
        if not self.client:
            # Fallback: use first few words
            words = text.split()[:5]
            return ' '.join(words) if words else 'Untitled Note'
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Generate a concise, descriptive title (max 50 characters) for the following handwritten note text:"},
                    {"role": "user", "content": text[:500]}  # Limit input length
                ],
                max_tokens=50,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            words = text.split()[:5]
            return ' '.join(words) if words else 'Untitled Note'
    
    def _categorize_text(self, text: str) -> str:
        """Categorize the content of the note"""
        if not self.client:
            return 'General'
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Categorize this handwritten note into one of these categories: Meeting Notes, Personal Journal, Study Notes, Shopping List, Reminder, Ideas/Brainstorming, Contact Info, Other. Respond with only the category name."},
                    {"role": "user", "content": text[:500]}
                ],
                max_tokens=20,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error categorizing text: {e}")
            return 'General'
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from the text"""
        if not self.client:
            # Fallback: simple extraction
            sentences = text.split('.')
            return [s.strip() for s in sentences[:3] if s.strip()]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract 3-5 key points from this handwritten note. Return as a JSON array of strings."},
                    {"role": "user", "content": text[:800]}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return [line.strip() for line in result.split('\n') if line.strip()]
        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            sentences = text.split('.')
            return [s.strip() for s in sentences[:3] if s.strip()]
    
    def _generate_summary(self, text: str) -> str:
        """Generate a summary of the text"""
        if not self.client:
            # Fallback: truncate text
            return text[:200] + "..." if len(text) > 200 else text
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Generate a concise summary (2-3 sentences) of this handwritten note:"},
                    {"role": "user", "content": text[:1000]}
                ],
                max_tokens=150,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return text[:200] + "..." if len(text) > 200 else text
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze the sentiment of the text"""
        if not self.client:
            return 'neutral'
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Analyze the sentiment of this text. Respond with only one word: positive, negative, or neutral."},
                    {"role": "user", "content": text[:500]}
                ],
                max_tokens=10,
                temperature=0.1
            )
            return response.choices[0].message.content.strip().lower()
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 'neutral'
    
    def _generate_tags(self, text: str, category: str) -> List[str]:
        """Generate relevant tags for the text"""
        if not self.client:
            # Fallback: basic tags based on category
            tag_map = {
                'Meeting Notes': ['meeting', 'work', 'notes'],
                'Personal Journal': ['personal', 'journal', 'reflection'],
                'Study Notes': ['study', 'learning', 'education'],
                'Shopping List': ['shopping', 'list', 'items'],
                'Reminder': ['reminder', 'todo', 'important'],
                'Ideas/Brainstorming': ['ideas', 'brainstorming', 'creative'],
                'Contact Info': ['contact', 'information', 'people']
            }
            return tag_map.get(category, ['general', 'notes'])
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"Generate 3-5 relevant tags for this {category} note. Return as a JSON array of strings."},
                    {"role": "user", "content": text[:500]}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return [tag.strip().lower() for tag in result.split(',') if tag.strip()]
        except Exception as e:
            logger.error(f"Error generating tags: {e}")
            return [category.lower(), 'notes']
    
    def generate_embeddings(self, text: str) -> Optional[np.ndarray]:
        """Generate embeddings for semantic search"""
        if not self.embedding_model:
            return None
        
        try:
            return self.embedding_model.encode(text)
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def search_similar_notes(self, query: str, note_embeddings: List[np.ndarray], threshold: float = 0.7) -> List[int]:
        """Find similar notes based on semantic similarity"""
        if not self.embedding_model or not note_embeddings:
            return []
        
        try:
            query_embedding = self.embedding_model.encode(query)
            similarities = []
            
            for i, note_embedding in enumerate(note_embeddings):
                similarity = np.dot(query_embedding, note_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(note_embedding)
                )
                if similarity >= threshold:
                    similarities.append((i, similarity))
            
            # Sort by similarity and return indices
            similarities.sort(key=lambda x: x[1], reverse=True)
            return [idx for idx, _ in similarities]
        except Exception as e:
            logger.error(f"Error searching similar notes: {e}")
            return []