#!/usr/bin/env python3
"""Generate plain PDF reports from markdown files."""

import re
from pathlib import Path
from fpdf import FPDF

PROJECT_ROOT = Path(__file__).parent


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f'{self.page_no()}', align='C')


def clean(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = text.replace('\u2014', '--').replace('\u2013', '-')
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2248', '~').replace('\u2265', '>=').replace('\u2264', '<=')
    text = text.replace('\u03b1', 'alpha').replace('\u2192', '->').replace('\u2022', '-')
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text


def parse_md(md_text):
    blocks = []
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('# '):
            blocks.append(('h1', line[2:].strip())); i += 1
        elif line.startswith('## '):
            blocks.append(('h2', line[3:].strip())); i += 1
        elif line.startswith('### '):
            blocks.append(('h3', line[4:].strip())); i += 1
        elif re.match(r'^!\[.*?\]\((.+?)\)', line):
            m = re.match(r'^!\[.*?\]\((.+?)\)', line)
            blocks.append(('image', m.group(1))); i += 1
        elif line.startswith('*') and line.endswith('*'):
            blocks.append(('caption', line.strip('* '))); i += 1
        elif '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
            headers = [c.strip() for c in line.split('|') if c.strip()]
            i += 2
            rows = []
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].split('|') if c.strip()])
                i += 1
            blocks.append(('table', (headers, rows)))
        elif line.strip().startswith('- '):
            bullets = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                bullets.append(lines[i].strip()[2:]); i += 1
            blocks.append(('bullets', bullets))
        elif line.strip():
            para = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') and not lines[i].startswith('|') and not lines[i].startswith('- ') and not lines[i].startswith('![') and not (lines[i].startswith('*') and lines[i].endswith('*')):
                para.append(lines[i].strip()); i += 1
            if para:
                blocks.append(('paragraph', ' '.join(para)))
        else:
            i += 1
    return blocks


def generate_pdf(md_path, pdf_path):
    md_text = md_path.read_text(encoding='utf-8')
    blocks = parse_md(md_text)
    pdf = ReportPDF()
    pdf.add_page()

    for btype, content in blocks:
        if pdf.get_y() > 260:
            pdf.add_page()

        if btype == 'h1':
            pdf.set_font('Helvetica', 'B', 16)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 8, clean(content))
            pdf.ln(4)

        elif btype == 'h2':
            if pdf.get_y() > 250: pdf.add_page()
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 13)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 7, clean(content))
            pdf.ln(2)

        elif btype == 'h3':
            if pdf.get_y() > 255: pdf.add_page()
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6, clean(content))
            pdf.ln(2)

        elif btype == 'paragraph':
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5.5, clean(content))
            pdf.ln(3)

        elif btype == 'bullets':
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for b in content:
                pdf.cell(5, 5.5, '-')
                pdf.multi_cell(0, 5.5, f' {clean(b)}')
                pdf.ln(1)
            pdf.ln(2)

        elif btype == 'caption':
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 4.5, clean(content), align='C')
            pdf.ln(3)

        elif btype == 'image':
            img_path = md_path.parent / content
            if img_path.exists():
                if pdf.get_y() > 180: pdf.add_page()
                try:
                    pdf.image(str(img_path), x=15, w=min(pdf.w - 30, 170))
                except Exception:
                    pass
                pdf.ln(2)

        elif btype == 'table':
            headers, rows = content
            if pdf.get_y() > 220: pdf.add_page()
            n = len(headers)
            col_w = (pdf.w - 30) / n
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(0, 0, 0)
            for h in headers:
                pdf.cell(col_w, 6, clean(h), border=1, align='C')
            pdf.ln()
            pdf.set_font('Helvetica', '', 9)
            for row in rows:
                for val in row:
                    pdf.cell(col_w, 5.5, clean(val), border=1, align='C')
                pdf.ln()
            pdf.ln(3)

    pdf.output(str(pdf_path))
    print(f'  {pdf_path.name} ({pdf_path.stat().st_size // 1024} KB)')


def main():
    parts = [
        ('part1_regression', 'part1_report'),
        ('part2_classification', 'part2_report'),
        ('part3_timeseries', 'part3_report'),
        ('part4_clustering', 'part4_report'),
    ]
    print('Generating PDFs...')
    for d, name in parts:
        md = PROJECT_ROOT / d / f'{name}.md'
        pdf = PROJECT_ROOT / d / f'{name}.pdf'
        if md.exists():
            generate_pdf(md, pdf)
    print('Done.')


if __name__ == '__main__':
    main()
