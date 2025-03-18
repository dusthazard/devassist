"""
Text tool for processing and manipulating text in development contexts.

This tool provides various text manipulation functions useful in development,
such as formatting, transformation, analysis, and generation of text content.
"""

import logging
import re
from typing import Dict, List, Any, Union
import string
import random
import json
import difflib

from devassist.tools.base.tool import BaseTool
from devassist.tools.base.tool_result import ToolResult

class TextTool(BaseTool):
    """
    A tool for processing and manipulating text in development contexts.
    
    Supports:
    - Text analysis (word count, character statistics)
    - Text transformation (case conversion, formatting)
    - Regular expression operations
    - Diff generation
    - Text generation (lorem ipsum, random strings)
    - Common text normalization tasks
    """
    
    name = "text"
    description = "Process and manipulate text for development tasks"
    category = "Utility"
    
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to process"
            },
            "operation": {
                "type": "string",
                "description": "The operation to perform",
                "enum": [
                    "analyze", "transform", "regex", "diff", "generate", 
                    "normalize", "excerpt", "format_json", "format_xml",
                    "camel_case", "snake_case", "kebab_case", "pascal_case"
                ]
            },
            "target_case": {
                "type": "string",
                "description": "Target case for case conversion",
                "enum": ["upper", "lower", "title", "camel", "pascal", "snake", "kebab"]
            },
            "pattern": {
                "type": "string",
                "description": "Regular expression pattern for regex operations"
            },
            "replacement": {
                "type": "string",
                "description": "Replacement string for regex replace operation"
            },
            "text2": {
                "type": "string",
                "description": "Second text for comparison operations"
            },
            "length": {
                "type": "integer",
                "description": "Length parameter for text generation",
                "default": 100
            },
            "format": {
                "type": "string",
                "description": "Format for output (e.g., 'json', 'html', 'markdown')"
            }
        },
        "required": ["text", "operation"]
    }
    
    def __init__(self):
        """Initialize the text tool."""
        self.logger = logging.getLogger("devassist.tools.text")
    
    def execute(self, text: str, operation: str, 
                target_case: str = None, pattern: str = None,
                replacement: str = None, text2: str = None,
                length: int = 100, format: str = None,
                **kwargs) -> Union[Dict[str, Any], ToolResult]:
        """
        Execute the text tool.
        
        Args:
            text: The text to process.
            operation: The operation to perform.
            target_case: Target case for case conversion.
            pattern: Regular expression pattern for regex operations.
            replacement: Replacement string for regex replace operation.
            text2: Second text for comparison operations.
            length: Length parameter for text generation.
            format: Format for output.
            **kwargs: Additional parameters.
            
        Returns:
            The operation result.
        """
        try:
            # Call the appropriate operation method
            if operation == "analyze":
                return self._analyze_text(text)
            elif operation == "transform":
                return self._transform_text(text, target_case)
            elif operation == "regex":
                return self._regex_operation(text, pattern, replacement)
            elif operation == "diff":
                return self._diff_texts(text, text2)
            elif operation == "generate":
                return self._generate_text(text, length)
            elif operation == "normalize":
                return self._normalize_text(text)
            elif operation == "excerpt":
                return self._create_excerpt(text, length)
            elif operation == "format_json":
                return self._format_json(text)
            elif operation == "format_xml":
                return self._format_xml(text)
            elif operation == "camel_case":
                return self._to_camel_case(text)
            elif operation == "snake_case":
                return self._to_snake_case(text)
            elif operation == "kebab_case":
                return self._to_kebab_case(text)
            elif operation == "pascal_case":
                return self._to_pascal_case(text)
            else:
                return ToolResult(
                    tool_name=self.name,
                    status="error",
                    error=f"Unsupported operation: {operation}"
                )
        except Exception as e:
            self.logger.error(f"Text tool error: {e}")
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Error in text operation: {str(e)}"
            )
    
    def _analyze_text(self, text: str) -> ToolResult:
        """
        Analyze text properties (word count, character statistics, etc.).
        
        Args:
            text: The text to analyze.
            
        Returns:
            A ToolResult with analysis results.
        """
        # Character count
        char_count = len(text)
        
        # Word count
        words = re.findall(r'\b\w+\b', text)
        word_count = len(words)
        
        # Line count
        lines = text.splitlines()
        line_count = len(lines)
        
        # Paragraph count (separated by double line breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraph_count = len(paragraphs)
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Sentence count
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Word frequency (top 10)
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Character distribution
        char_dist = {}
        for char in text:
            if char in char_dist:
                char_dist[char] += 1
            else:
                char_dist[char] = 1
        
        # Readability score (simple approximation of Flesch-Kincaid)
        if word_count > 0 and sentence_count > 0:
            words_per_sentence = word_count / sentence_count
            readability = 206.835 - (1.015 * words_per_sentence) - (84.6 * (sum(len(word) for word in words) / word_count))
        else:
            readability = 0
        
        return ToolResult(
            tool_name=self.name,
            status="success",
            result={
                "char_count": char_count,
                "word_count": word_count,
                "line_count": line_count,
                "paragraph_count": paragraph_count,
                "sentence_count": sentence_count,
                "avg_word_length": round(avg_word_length, 2),
                "top_words": dict(top_words),
                "readability_score": round(readability, 2),
                "summary": f"Text contains {char_count} characters, {word_count} words, {line_count} lines, {paragraph_count} paragraphs"
            }
        )
    
    def _transform_text(self, text: str, target_case: str) -> ToolResult:
        """
        Transform text (case conversion, etc.).
        
        Args:
            text: The text to transform.
            target_case: Target case for conversion.
            
        Returns:
            A ToolResult with transformed text.
        """
        if not target_case:
            return ToolResult(
                tool_name=self.name,
                status="error",
                error="Target case not specified"
            )
        
        result_text = text
        case_description = target_case
        
        if target_case == "upper":
            result_text = text.upper()
            case_description = "UPPERCASE"
        elif target_case == "lower":
            result_text = text.lower()
            case_description = "lowercase"
        elif target_case == "title":
            result_text = text.title()
            case_description = "Title Case"
        elif target_case == "camel":
            result_text = self._to_camel_case(text)["transformed_text"]
            case_description = "camelCase"
        elif target_case == "pascal":
            result_text = self._to_pascal_case(text)["transformed_text"]
            case_description = "PascalCase"
        elif target_case == "snake":
            result_text = self._to_snake_case(text)["transformed_text"]
            case_description = "snake_case"
        elif target_case == "kebab":
            result_text = self._to_kebab_case(text)["transformed_text"]
            case_description = "kebab-case"
        else:
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Unsupported target case: {target_case}"
            )
        
        return ToolResult(
            tool_name=self.name,
            status="success",
            result={
                "original_text": text,
                "transformed_text": result_text,
                "transformation": f"Converted to {case_description}",
                "char_diff": len(result_text) - len(text)
            }
        )
    
    def _regex_operation(self, text: str, pattern: str, replacement: str) -> ToolResult:
        """
        Perform regex operations (match, replace, etc.).
        
        Args:
            text: The text to process.
            pattern: Regex pattern.
            replacement: Replacement string (for replace operation).
            
        Returns:
            A ToolResult with regex operation results.
        """
        if not pattern:
            return ToolResult(
                tool_name=self.name,
                status="error",
                error="Regex pattern not specified"
            )
        
        try:
            # Compile the regex
            regex = re.compile(pattern)
            
            # Find all matches
            matches = regex.findall(text)
            
            # Perform replacement if specified
            replaced_text = text
            if replacement is not None:
                replaced_text = regex.sub(replacement, text)
            
            # Count matches
            match_count = len(matches)
            
            # Extract groups if present
            groups = []
            for match in regex.finditer(text):
                if match.groups():
                    groups.append(match.groups())
            
            return ToolResult(
                tool_name=self.name,
                status="success",
                result={
                    "pattern": pattern,
                    "matches": matches[:20],  # Limit to first 20 matches
                    "match_count": match_count,
                    "groups": groups[:20],  # Limit to first 20 group sets
                    "replaced_text": replaced_text if replacement is not None else None,
                    "summary": f"Found {match_count} matches with pattern '{pattern}'"
                }
            )
        except re.error as e:
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Invalid regex pattern: {str(e)}"
            )
    
    def _diff_texts(self, text1: str, text2: str) -> ToolResult:
        """
        Generate diff between two texts.
        
        Args:
            text1: First text.
            text2: Second text.
            
        Returns:
            A ToolResult with diff results.
        """
        if text2 is None:
            return ToolResult(
                tool_name=self.name,
                status="error",
                error="Second text not provided for diff"
            )
        
        # Split texts into lines
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        # Generate diff
        differ = difflib.Differ()
        diff = list(differ.compare(lines1, lines2))
        
        # Calculate diff statistics
        added_lines = sum(1 for line in diff if line.startswith("+ "))
        removed_lines = sum(1 for line in diff if line.startswith("- "))
        changed_lines = sum(1 for line in diff if line.startswith("? "))
        
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        return ToolResult(
            tool_name=self.name,
            status="success",
            result={
                "diff": diff,
                "added_lines": added_lines,
                "removed_lines": removed_lines,
                "changed_lines": changed_lines,
                "similarity": round(similarity * 100, 2),
                "summary": f"Diff shows {added_lines} added, {removed_lines} removed, and {changed_lines} changed lines. Similarity: {round(similarity * 100, 2)}%"
            }
        )
    
    def _generate_text(self, text_type: str, length: int) -> ToolResult:
        """
        Generate text (lorem ipsum, random strings, etc.).
        
        Args:
            text_type: Type of text to generate.
            length: Length of text to generate.
            
        Returns:
            A ToolResult with generated text.
        """
        # Normalize text type
        text_type = text_type.lower()
        
        # Ensure length is reasonable
        length = min(max(1, length), 10000)  # Limit between 1 and 10000
        
        if text_type in ["lorem", "lorem ipsum"]:
            generated_text = self._generate_lorem_ipsum(length)
            description = "Lorem Ipsum text"
        elif text_type in ["random", "random string"]:
            generated_text = self._generate_random_string(length)
            description = "Random string"
        elif text_type in ["uuid", "guid"]:
            import uuid
            generated_text = str(uuid.uuid4())
            description = "UUID/GUID"
        elif text_type in ["password", "random password"]:
            generated_text = self._generate_random_password(length)
            description = "Random password"
        elif text_type in ["html", "sample html"]:
            generated_text = self._generate_sample_html(length)
            description = "Sample HTML"
        elif text_type in ["markdown", "sample markdown"]:
            generated_text = self._generate_sample_markdown(length)
            description = "Sample Markdown"
        elif text_type in ["json", "sample json"]:
            generated_text = self._generate_sample_json(length)
            description = "Sample JSON"
        else:
            # Default to lorem ipsum
            generated_text = self._generate_lorem_ipsum(length)
            description = "Lorem Ipsum text (default)"
        
        return ToolResult(
            tool_name=self.name,
            status="success",
            result={
                "text_type": text_type,
                "length": len(generated_text),
                "generated_text": generated_text,
                "description": description
            }
        )
    
    def _normalize_text(self, text: str) -> ToolResult:
        """
        Normalize text (remove extra whitespace, normalize line endings, etc.).
        
        Args:
            text: The text to normalize.
            
        Returns:
            A ToolResult with normalized text.
        """
        # Original text stats
        original_length = len(text)
        original_lines = len(text.splitlines())
        
        # Normalize line endings (convert to \n)
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # Remove trailing whitespace from lines
        normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
        
        # Remove duplicate blank lines
        normalized = re.sub(r'\n\s*\n\s*\n+', '\n\n', normalized)
        
        # Remove trailing blank lines
        normalized = normalized.rstrip() + ("\n" if text.endswith("\n") else "")
        
        # Normalized text stats
        normalized_length = len(normalized)
        normalized_lines = len(normalized.splitlines())
        
        return ToolResult(
            tool_name=self.name,
            status="success",
            result={
                "original_text": text,
                "normalized_text": normalized,
                "original_length": original_length,
                "normalized_length": normalized_length,
                "original_lines": original_lines,
                "normalized_lines": normalized_lines,
                "bytes_removed": original_length - normalized_length,
                "summary": f"Normalized text. Removed {original_length - normalized_length} characters."
            }
        )
    
    def _create_excerpt(self, text: str, length: int = 100) -> ToolResult:
        """
        Create an excerpt from text.
        
        Args:
            text: The text to excerpt.
            length: Maximum length of excerpt.
            
        Returns:
            A ToolResult with excerpted text.
        """
        # Ensure length is reasonable
        length = min(max(10, length), 1000)  # Limit between 10 and 1000
        
        # If text is shorter than length, return it as is
        if len(text) <= length:
            return ToolResult(
                tool_name=self.name,
                status="success",
                result={
                    "original_text": text,
                    "excerpt": text,
                    "length": len(text),
                    "truncated": False
                }
            )
        
        # Try to break at a sentence boundary
        sentences = re.split(r'(?<=[.!?])\s+', text)
        excerpt = ""
        for sentence in sentences:
            if len(excerpt + sentence) <= length:
                excerpt += sentence + " "
            else:
                break
        
        # If no sentence boundaries or very long first sentence
        if not excerpt or len(excerpt) < length / 2:
            # Try to break at a word boundary
            words = text.split()
            excerpt = ""
            for word in words:
                if len(excerpt + word) <= length - 3:  # Leave room for ellipsis
                    excerpt += word + " "
                else:
                    break
            
            excerpt = excerpt.rstrip() + "..."
        else:
            excerpt = excerpt.rstrip()
            if len(text) > len(excerpt):
                excerpt += "..."
        
        return ToolResult(
            tool_name=self.name,
            status="success",
            result={
                "original_text": text,
                "excerpt": excerpt,
                "length": len(excerpt),
                "truncated": True,
                "original_length": len(text)
            }
        )
    
    def _format_json(self, text: str) -> ToolResult:
        """
        Format JSON text.
        
        Args:
            text: The JSON text to format.
            
        Returns:
            A ToolResult with formatted JSON.
        """
        try:
            # Parse JSON
            parsed_json = json.loads(text)
            
            # Format with indentation
            formatted_json = json.dumps(parsed_json, indent=2, sort_keys=False)
            
            return ToolResult(
                tool_name=self.name,
                status="success",
                result={
                    "original_text": text,
                    "formatted_text": formatted_json,
                    "json_type": type(parsed_json).__name__,
                    "item_count": len(parsed_json) if isinstance(parsed_json, (list, dict)) else 1,
                    "valid_json": True
                }
            )
        except json.JSONDecodeError as e:
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"Invalid JSON: {str(e)}"
            )
    
    def _format_xml(self, text: str) -> ToolResult:
        """
        Format XML text.
        
        Args:
            text: The XML text to format.
            
        Returns:
            A ToolResult with formatted XML.
        """
        try:
            import xml.dom.minidom as md
            
            # Parse and pretty-print XML
            dom = md.parseString(text)
            formatted_xml = dom.toprettyxml(indent="  ")
            
            # Remove extra newlines (minidom can add too many)
            formatted_xml = re.sub(r'\n\s*\n', '\n', formatted_xml)
            
            return ToolResult(
                tool_name=self.name,
                status="success",
                result={
                    "original_text": text,
                    "formatted_text": formatted_xml,
                    "valid_xml": True
                }
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                status="error",
                error=f"XML formatting error: {str(e)}"
            )
    
    def _to_camel_case(self, text: str) -> Dict[str, Any]:
        """
        Convert text to camelCase.
        
        Args:
            text: The text to convert.
            
        Returns:
            A dictionary with the conversion result.
        """
        # Remove special characters and split
        words = re.findall(r'\w+', text)
        if not words:
            return {"transformed_text": text}
        
        # Convert to camelCase
        result = words[0].lower()
        for word in words[1:]:
            if word:
                result += word[0].upper() + word[1:].lower()
        
        return {"transformed_text": result}
    
    def _to_snake_case(self, text: str) -> Dict[str, Any]:
        """
        Convert text to snake_case.
        
        Args:
            text: The text to convert.
            
        Returns:
            A dictionary with the conversion result.
        """
        # Handle camelCase and PascalCase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        
        # Remove special characters and replace spaces with underscores
        words = re.findall(r'\w+', s2.lower())
        result = '_'.join(words)
        
        return {"transformed_text": result}
    
    def _to_kebab_case(self, text: str) -> Dict[str, Any]:
        """
        Convert text to kebab-case.
        
        Args:
            text: The text to convert.
            
        Returns:
            A dictionary with the conversion result.
        """
        # First convert to snake_case
        snake = self._to_snake_case(text)["transformed_text"]
        
        # Replace underscores with hyphens
        result = snake.replace('_', '-')
        
        return {"transformed_text": result}
    
    def _to_pascal_case(self, text: str) -> Dict[str, Any]:
        """
        Convert text to PascalCase.
        
        Args:
            text: The text to convert.
            
        Returns:
            A dictionary with the conversion result.
        """
        # Remove special characters and split
        words = re.findall(r'\w+', text)
        if not words:
            return {"transformed_text": text}
        
        # Convert to PascalCase
        result = ''.join(word[0].upper() + word[1:].lower() for word in words if word)
        
        return {"transformed_text": result}
    
    def _generate_lorem_ipsum(self, length: int) -> str:
        """
        Generate Lorem Ipsum text.
        
        Args:
            length: Approximate length of text to generate.
            
        Returns:
            Generated Lorem Ipsum text.
        """
        paragraphs = [
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
            "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.",
            "Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit.",
            "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi."
        ]
        
        # Generate text by repeating paragraphs until we reach the desired length
        result = ""
        while len(result) < length:
            paragraph = random.choice(paragraphs)
            if len(result) + len(paragraph) + 2 <= length:
                result += paragraph + "\n\n"
            else:
                remaining = length - len(result)
                result += paragraph[:remaining]
                break
        
        return result.strip()
    
    def _generate_random_string(self, length: int) -> str:
        """
        Generate a random string.
        
        Args:
            length: Length of string to generate.
            
        Returns:
            A random string.
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _generate_random_password(self, length: int) -> str:
        """
        Generate a random password.
        
        Args:
            length: Length of password to generate.
            
        Returns:
            A random password.
        """
        # Ensure minimum length
        length = max(8, length)
        
        # Character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%^&*()-_=+[]{}|;:,.<>?'
        
        # Ensure at least one character from each set
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special)
        ]
        
        # Fill the rest
        all_chars = lowercase + uppercase + digits + special
        password.extend(random.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle
        random.shuffle(password)
        
        return ''.join(password)
    
    def _generate_sample_html(self, length: int) -> str:
        """
        Generate sample HTML.
        
        Args:
            length: Approximate length of HTML to generate.
            
        Returns:
            Sample HTML code.
        """
        # Basic HTML template
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample HTML</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        header {
            background-color: #f4f4f4;
            padding: 20px;
            text-align: center;
        }
        footer {
            background-color: #f4f4f4;
            padding: 10px;
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Sample HTML Page</h1>
        </header>
        <main>
            <section>
                <h2>Section Title</h2>
                <p>This is a paragraph of text. Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
                <p>Another paragraph with some more text.</p>
                <ul>
                    <li>List item one</li>
                    <li>List item two</li>
                    <li>List item three</li>
                </ul>
            </section>
            <section>
                <h2>Another Section</h2>
                <p>More content goes here.</p>
                <a href="#">This is a link</a>
            </section>
        </main>
        <footer>
            <p>&copy; 2025 Sample Page</p>
        </footer>
    </div>
</body>
</html>"""
        
        # If the template is too long, truncate it
        if len(html_template) > length:
            # Find a good closing point
            closing_tags = ["</div>", "</body>", "</html>"]
            for tag in closing_tags:
                pos = html_template[:length].rfind(tag)
                if pos > 0:
                    return html_template[:pos + len(tag)]
            
            # If no good closing point, just truncate
            return html_template[:length]
        
        return html_template
    
    def _generate_sample_markdown(self, length: int) -> str:
        """
        Generate sample Markdown.
        
        Args:
            length: Approximate length of Markdown to generate.
            
        Returns:
            Sample Markdown text.
        """
        md_template = """# Sample Markdown Document

## Introduction

This is a sample Markdown document that demonstrates various Markdown features.

## Text Formatting

You can format text in *italic* or **bold**. You can also use ***bold italic***.

## Lists

### Unordered Lists

- Item 1
- Item 2
- Item 3
  - Nested item 1
  - Nested item 2

### Ordered Lists

1. First item
2. Second item
3. Third item

## Links and Images

[Link to Google](https://www.google.com)

![Sample Image](https://example.com/image.jpg)

## Code

Inline code: `console.log('Hello, world!');`

Code block:

```javascript
function greet(name) {
  return `Hello, ${name}!`;
}
console.log(greet('World'));
```

## Blockquotes

> This is a blockquote.
> It can span multiple lines.

## Tables

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |

## Horizontal Rule

---

## Task Lists

- [x] Completed task
- [ ] Incomplete task
- [ ] Another incomplete task"""
        
        # If the template is too long, truncate it at a section boundary
        if len(md_template) > length:
            sections = md_template.split("## ")
            result = sections[0]
            i = 1
            while i < len(sections) and len(result + "## " + sections[i]) <= length:
                result += "## " + sections[i]
                i += 1
            
            return result
        
        return md_template
    
    def _generate_sample_json(self, length: int) -> str:
        """
        Generate sample JSON.
        
        Args:
            length: Approximate length of JSON to generate.
            
        Returns:
            Sample JSON text.
        """
        # Basic JSON template
        json_template = {
            "id": 12345,
            "name": "Sample Project",
            "description": "This is a sample JSON document for demonstration purposes.",
            "version": "1.0.0",
            "created_at": "2025-03-17T12:00:00Z",
            "author": {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com",
                "role": "Developer"
            },
            "tags": ["sample", "json", "demo", "example"],
            "settings": {
                "public": True,
                "notifications": False,
                "theme": "light"
            },
            "items": [
                {
                    "id": 1,
                    "name": "Item 1",
                    "quantity": 10,
                    "active": True
                },
                {
                    "id": 2,
                    "name": "Item 2",
                    "quantity": 5,
                    "active": False
                },
                {
                    "id": 3,
                    "name": "Item 3",
                    "quantity": 15,
                    "active": True
                }
            ],
            "metadata": {
                "created_by": "system",
                "last_modified": "2025-03-17T14:30:00Z",
                "views": 1024,
                "rating": 4.5
            }
        }
        
        json_str = json.dumps(json_template, indent=2)
        
        # If the template is too long, simplify it
        if len(json_str) > length:
            # Remove items one by one until it fits
            simple_json = json_template.copy()
            
            # Simplify the items array
            while "items" in simple_json and len(json.dumps(simple_json, indent=2)) > length:
                simple_json["items"].pop()
                if not simple_json["items"]:
                    del simple_json["items"]
            
            # Remove metadata if still too long
            if "metadata" in simple_json and len(json.dumps(simple_json, indent=2)) > length:
                del simple_json["metadata"]
            
            # Remove author if still too long
            if "author" in simple_json and len(json.dumps(simple_json, indent=2)) > length:
                del simple_json["author"]
            
            # Remove settings if still too long
            if "settings" in simple_json and len(json.dumps(simple_json, indent=2)) > length:
                del simple_json["settings"]
            
            # As a last resort, return a minimal JSON object
            if len(json.dumps(simple_json, indent=2)) > length:
                simple_json = {
                    "id": 12345,
                    "name": "Sample Project",
                    "version": "1.0.0"
                }
            
            json_str = json.dumps(simple_json, indent=2)
        
        return json_str
