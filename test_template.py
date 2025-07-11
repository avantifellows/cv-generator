#!/usr/bin/env python3
"""Test script to verify the HTML template system works correctly"""

import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import filter_empty_sections, render_template, create_filename

def load_test_data():
    """Load test data from JSON file"""
    with open('test_data.json', 'r') as f:
        return json.load(f)

def test_template_system():
    print("=== CV Template System Test ===")
    
    # Load test data from JSON
    test_data = load_test_data()
    print(f"✓ Test data loaded from test_data.json")
    print(f"  Name: {test_data['personal_info']['full_name']}")
    print(f"  Education entries: {len(test_data['education'])}")
    print(f"  Achievement entries: {len(test_data['achievements'])}")
    print(f"  Internship entries: {len(test_data['internships'])}")
    print(f"  Project entries: {len(test_data['projects'])}")
    print(f"  POR entries: {len(test_data['positions_of_responsibility'])}")
    print(f"  Extracurricular entries: {len(test_data['extracurricular'])}")
    print(f"  Technical skills: {len(test_data['technical_skills'])}")
    
    # Filter data (remove any empty sections)
    filtered_data = filter_empty_sections(test_data)
    print(f"\n✓ Data filtered successfully")
    
    # Generate HTML for display
    print(f"\n=== Generating HTML for Display ===")
    html_output = render_template('cv_template.html', filtered_data)
    print(f"✓ HTML template rendered ({len(html_output)} characters)")
    
    # Save HTML file
    html_filename = f"test_cv_{create_filename(test_data['personal_info']['full_name'])}.html"
    html_path = f"generated/{html_filename}"
    os.makedirs('generated', exist_ok=True)
    
    with open(html_path, 'w') as f:
        f.write(html_output)
    print(f"✓ HTML saved to: {html_path}")
    
    # Generate PDF HTML template
    print(f"\n=== Generating PDF HTML Template ===")
    try:
        pdf_html_output = render_template('cv_template_pdf.html', filtered_data)
        print(f"✓ PDF HTML template rendered ({len(pdf_html_output)} characters)")
        
        # Save PDF HTML file
        pdf_html_filename = f"test_cv_{create_filename(test_data['personal_info']['full_name'])}_pdf.html"
        pdf_html_path = f"generated/{pdf_html_filename}"
        
        with open(pdf_html_path, 'w') as f:
            f.write(pdf_html_output)
        print(f"✓ PDF HTML saved to: {pdf_html_path}")
        
        # Test PDF generation using WeasyPrint
        print(f"\n=== Testing PDF Generation ===")
        try:
            import weasyprint
            pdf_bytes = weasyprint.HTML(string=pdf_html_output).write_pdf()
            
            pdf_filename = f"test_cv_{create_filename(test_data['personal_info']['full_name'])}.pdf"
            pdf_path = f"generated/{pdf_filename}"
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            print(f"✓ PDF generated successfully: {pdf_path}")
            
            # Get file size
            file_size = os.path.getsize(pdf_path)
            print(f"  PDF size: {file_size:,} bytes")
            
        except Exception as e:
            print(f"⚠ Error generating PDF: {e}")
        
    except Exception as e:
        print(f"⚠ Error rendering PDF template: {e}")
    
    # Content validation
    print(f"\n=== Content Validation ===")
    
    name = test_data['personal_info']['full_name']
    
    # Check HTML content
    if name in html_output:
        print("✓ Personal info rendered in HTML")
    
    if "Stanford University" in html_output:
        print("✓ Education section rendered in HTML")
    
    if "Dean's List" in html_output:
        print("✓ Achievements section rendered in HTML")
    
    if "Google" in html_output:
        print("✓ Internships section rendered in HTML")
    
    if "AI-Powered Code Review" in html_output:
        print("✓ Projects section rendered in HTML")
    
    if "Computer Science Society" in html_output:
        print("✓ Positions of Responsibility rendered in HTML")
    
    if "Marathon running" in html_output:
        print("✓ Extracurricular activities rendered in HTML")
    
    if "Python" in html_output and "JavaScript" in html_output:
        print("✓ Technical skills rendered in HTML")
    
    # Check for unreplaced variables
    if "{{" in html_output:
        print("⚠ Warning: Found unreplaced Jinja2 variables in HTML")
    else:
        print("✓ No unreplaced variables in HTML")
    
    print(f"\n=== Test Summary ===")
    print(f"HTML file: {html_path}")
    if 'pdf_html_path' in locals():
        print(f"PDF HTML file: {pdf_html_path}")
    if 'pdf_path' in locals() and os.path.exists(pdf_path):
        print(f"PDF file: {pdf_path}")
    
    print(f"\n=== Test Complete ===")
    return {
        'html_output': html_output,
        'html_path': html_path,
        'pdf_html_output': pdf_html_output if 'pdf_html_output' in locals() else None,
        'pdf_html_path': pdf_html_path if 'pdf_html_path' in locals() else None
    }

if __name__ == "__main__":
    test_template_system()