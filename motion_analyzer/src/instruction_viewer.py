#!/usr/bin/env python3
"""
Instruction Viewer and Analyzer
Creates HTML pages for viewing instructions and analyzing recordings against them.
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class InstructionViewer:
    """Generate HTML viewer for instructions with slide navigation."""

    def __init__(self, markdown_file: str, json_file: str, output_dir: str = None):
        """Initialize viewer with markdown and JSON files."""
        self.markdown_file = Path(markdown_file)
        self.json_file = Path(json_file)

        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        # Set up output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.markdown_file.parent / "html_viewer"

        self.output_dir.mkdir(exist_ok=True)

    def generate_slide_html(self, slide: Dict) -> str:
        """Generate HTML for a single slide."""
        html_parts = []

        # Slide header
        slide_title = slide.get('title', f"Slide {slide['slide_number']}")
        html_parts.append(f'<div class="slide" id="slide-{slide["slide_number"]}">')
        html_parts.append(f'<h2 class="slide-title">{slide_title}</h2>')
        html_parts.append(f'<div class="slide-meta">Slide {slide["slide_number"]} | Layout: {slide["layout"]}</div>')

        # Content sections
        if slide.get('content'):
            html_parts.append('<div class="slide-content">')
            for item in slide['content']:
                content_text = item['content'].replace('\n', '<br>')
                html_parts.append(f'<div class="content-item">{content_text}</div>')
            html_parts.append('</div>')

        # Tables
        if slide.get('tables'):
            html_parts.append('<div class="slide-tables">')
            for table in slide['tables']:
                html_parts.append('<div class="table-container">')
                # Convert markdown table to HTML
                table_html = self.markdown_table_to_html(table['content'])
                html_parts.append(table_html)
                html_parts.append('</div>')
            html_parts.append('</div>')

        # Images
        if slide.get('images'):
            html_parts.append('<div class="slide-images">')
            for img in slide['images']:
                img_path = f"../{img['path']}"
                html_parts.append(f'''
                    <div class="image-container">
                        <img src="{img_path}" alt="{img['alt_text']}" onclick="openImageModal(this)">
                        <div class="image-caption">{img['alt_text']}</div>
                    </div>
                ''')
            html_parts.append('</div>')

        # Speaker notes
        if slide.get('notes'):
            html_parts.append('<div class="slide-notes">')
            html_parts.append('<h4>Speaker Notes:</h4>')
            html_parts.append(f'<p>{slide["notes"]}</p>')
            html_parts.append('</div>')

        html_parts.append('</div>')

        return '\n'.join(html_parts)

    def markdown_table_to_html(self, markdown_table: str) -> str:
        """Convert markdown table to HTML table."""
        lines = markdown_table.strip().split('\n')
        if len(lines) < 3:
            return f'<pre>{markdown_table}</pre>'

        html_parts = ['<table class="data-table">']

        # Process header
        header_line = lines[0]
        headers = [h.strip() for h in header_line.split('|')[1:-1]]
        html_parts.append('<thead><tr>')
        for header in headers:
            html_parts.append(f'<th>{header}</th>')
        html_parts.append('</tr></thead>')

        # Process data rows (skip separator line)
        html_parts.append('<tbody>')
        for line in lines[2:]:
            cells = [c.strip() for c in line.split('|')[1:-1]]
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')

        html_parts.append('</table>')
        return '\n'.join(html_parts)

    def generate_navigation_html(self) -> str:
        """Generate navigation sidebar HTML."""
        nav_parts = ['<div class="navigation">']
        nav_parts.append('<h3>Slides</h3>')
        nav_parts.append('<ul class="slide-nav">')

        for slide in self.data['slides']:
            slide_num = slide['slide_number']
            title = slide.get('title', f'Slide {slide_num}')
            if len(title) > 30:
                title = title[:27] + '...'
            nav_parts.append(f'''
                <li>
                    <a href="#slide-{slide_num}" onclick="goToSlide({slide_num}); return false;">
                        <span class="slide-num">{slide_num}.</span>
                        <span class="slide-title-nav">{title}</span>
                    </a>
                </li>
            ''')

        nav_parts.append('</ul>')
        nav_parts.append('</div>')

        return '\n'.join(nav_parts)

    def generate_html(self) -> str:
        """Generate complete HTML document."""
        metadata = self.data['metadata']
        slides_html = []

        for slide in self.data['slides']:
            slides_html.append(self.generate_slide_html(slide))

        navigation_html = self.generate_navigation_html()

        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata['title']} - Instruction Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
        }}

        .container {{
            display: flex;
            width: 100%;
            height: 100vh;
        }}

        .navigation {{
            width: 250px;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }}

        .navigation h3 {{
            margin-bottom: 20px;
            color: #333;
            font-size: 18px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}

        .slide-nav {{
            list-style: none;
        }}

        .slide-nav li {{
            margin-bottom: 8px;
        }}

        .slide-nav a {{
            display: block;
            padding: 8px 12px;
            text-decoration: none;
            color: #555;
            border-radius: 5px;
            transition: all 0.3s ease;
        }}

        .slide-nav a:hover {{
            background: #f0f0f0;
            color: #667eea;
        }}

        .slide-nav a.active {{
            background: #667eea;
            color: white;
        }}

        .slide-num {{
            font-weight: bold;
            margin-right: 8px;
        }}

        .main-content {{
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            position: relative;
        }}

        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}

        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }}

        .metadata-item {{
            display: flex;
            align-items: center;
        }}

        .metadata-item strong {{
            margin-right: 5px;
            color: #444;
        }}

        .slides-container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .slide {{
            display: none;
            animation: fadeIn 0.5s;
        }}

        .slide.active {{
            display: block;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .slide-title {{
            color: #333;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}

        .slide-meta {{
            font-size: 14px;
            color: #666;
            margin-bottom: 20px;
        }}

        .slide-content {{
            margin-bottom: 20px;
        }}

        .content-item {{
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            margin-bottom: 10px;
            border-radius: 5px;
        }}

        .slide-tables {{
            margin-bottom: 20px;
        }}

        .table-container {{
            margin-bottom: 15px;
            overflow-x: auto;
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}

        .data-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        .data-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }}

        .data-table tr:hover {{
            background: #f5f5f5;
        }}

        .slide-images {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .image-container {{
            text-align: center;
        }}

        .image-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.15);
            cursor: pointer;
            transition: transform 0.3s ease;
        }}

        .image-container img:hover {{
            transform: scale(1.05);
        }}

        .image-caption {{
            margin-top: 8px;
            font-size: 14px;
            color: #666;
            font-style: italic;
        }}

        .slide-notes {{
            background: #fff9e6;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}

        .slide-notes h4 {{
            color: #996600;
            margin-bottom: 10px;
        }}

        .controls {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            gap: 10px;
            z-index: 100;
        }}

        .control-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }}

        .control-btn:hover {{
            background: #5a67d8;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }}

        .control-btn:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}

        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }}

        .modal-content {{
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
            margin-top: 50px;
        }}

        .close-modal {{
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}

        .close-modal:hover {{
            color: #667eea;
        }}

        @media (max-width: 768px) {{
            .container {{
                flex-direction: column;
            }}

            .navigation {{
                width: 100%;
                height: auto;
                position: sticky;
                top: 0;
                z-index: 50;
            }}

            .controls {{
                bottom: 10px;
                right: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {navigation_html}

        <div class="main-content">
            <div class="header">
                <h1>{metadata['title']}</h1>
                <div class="metadata">
                    <div class="metadata-item">
                        <strong>Author:</strong> {metadata['author']}
                    </div>
                    <div class="metadata-item">
                        <strong>Total Slides:</strong> {metadata['slide_count']}
                    </div>
                    <div class="metadata-item">
                        <strong>Modified:</strong> {metadata['modified'][:10] if metadata['modified'] else 'N/A'}
                    </div>
                    <div class="metadata-item">
                        <strong>Converted:</strong> {metadata['converted_date'][:10]}
                    </div>
                </div>
            </div>

            <div class="slides-container">
                {' '.join(slides_html)}
            </div>
        </div>
    </div>

    <div class="controls">
        <button class="control-btn" id="prevBtn" onclick="previousSlide()">← Previous</button>
        <button class="control-btn" id="nextBtn" onclick="nextSlide()">Next →</button>
    </div>

    <div id="imageModal" class="modal" onclick="closeImageModal()">
        <span class="close-modal">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>

    <script>
        let currentSlide = 1;
        const totalSlides = {metadata['slide_count']};

        function goToSlide(slideNum) {{
            // Hide all slides
            document.querySelectorAll('.slide').forEach(slide => {{
                slide.classList.remove('active');
            }});

            // Show current slide
            const targetSlide = document.getElementById(`slide-${{slideNum}}`);
            if (targetSlide) {{
                targetSlide.classList.add('active');
                currentSlide = slideNum;
            }}

            // Update navigation
            document.querySelectorAll('.slide-nav a').forEach(link => {{
                link.classList.remove('active');
            }});
            const activeLink = document.querySelector(`.slide-nav a[href="#slide-${{slideNum}}"]`);
            if (activeLink) {{
                activeLink.classList.add('active');
            }}

            // Update button states
            document.getElementById('prevBtn').disabled = currentSlide === 1;
            document.getElementById('nextBtn').disabled = currentSlide === totalSlides;

            // Scroll to top of content
            document.querySelector('.main-content').scrollTop = 0;
        }}

        function nextSlide() {{
            if (currentSlide < totalSlides) {{
                goToSlide(currentSlide + 1);
            }}
        }}

        function previousSlide() {{
            if (currentSlide > 1) {{
                goToSlide(currentSlide - 1);
            }}
        }}

        function openImageModal(img) {{
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            modal.style.display = 'block';
            modalImg.src = img.src;
        }}

        function closeImageModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}

        // Keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowLeft') previousSlide();
            if (e.key === 'ArrowRight') nextSlide();
            if (e.key === 'Escape') closeImageModal();
        }});

        // Initialize
        goToSlide(1);
    </script>
</body>
</html>'''

        return html_template

    def save_html(self) -> str:
        """Save HTML file."""
        html_content = self.generate_html()
        output_file = self.output_dir / f"{self.markdown_file.stem}.html"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML viewer created: {output_file}")
        return str(output_file)


def main():
    """Main function for command-line usage."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python instruction_viewer.py <markdown_file> <json_file> [output_dir]")
        sys.exit(1)

    md_file = sys.argv[1]
    json_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None

    viewer = InstructionViewer(md_file, json_file, output_dir)
    html_file = viewer.save_html()

    return html_file


if __name__ == "__main__":
    main()