# Notion Content Best Practices

To ensure high-quality, readable, and well-formatted Notion pages, all content should adhere to these guidelines:

## 1. Hierarchy and Structure
- **Headings**: Use `heading_2` for major sections and `heading_3` for sub-sections. Avoid overusing `heading_1` as the page title usually serves that role.
- **Table of Contents**: For long articles, consider if the structure supports a Table of Contents (Notion's `/toc` block).
- **Dividers**: Use dividers (`---`) to visually separate distinct major sections.

## 2. Readability & Formatting
- **Paragraph Length**: Keep paragraphs concise. Break walls of text (over 150-200 words) into smaller blocks.
- **Emphasis**: Use **bold** for key terms and *italics* for emphasis sparingly.
- **Lists**: Use bulleted or numbered lists for steps, features, or items to improve scannability.
- **Quotes**: Use the `quote` block for testimonials, important excerpts, or "key takeaways".

## 3. Visual & Interactive Elements
- **Callouts**: Use `callout` blocks (with relevant icons) for "Pro Tips", "Warnings", or "Summary" boxes.
- **Toggle Lists**: Use `toggle` blocks to hide dense technical details or FAQ-style content, keeping the page clean.
- **Code Blocks**: Always use `code` blocks for code snippets, specifying the correct language for syntax highlighting.

## 4. Technical Constraints (Notion API)
- **Character Limits**: Individual text elements must be under 2,000 characters. 
- **Block Limits**: A single request cannot exceed 100 blocks. Content must be batched.

## 5. Metadata
- Every page should have a clear **Title**, **Tags**, and a **Summary** (which can be used in database properties).
