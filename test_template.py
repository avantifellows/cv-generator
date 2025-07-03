#!/usr/bin/env python3
"""Test script to verify the new template system works correctly"""

import sys
import os
import json
import subprocess
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
    
    # Generate LaTeX
    print(f"\n=== Generating LaTeX ===")
    latex_output = render_template('cv_template.tex', filtered_data)
    print(f"✓ LaTeX template rendered ({len(latex_output)} characters)")
    
    # Save LaTeX file
    latex_filename = f"test_cv_{create_filename(test_data['personal_info']['full_name'])}.tex"
    latex_path = f"generated/{latex_filename}"
    os.makedirs('generated', exist_ok=True)
    
    with open(latex_path, 'w') as f:
        f.write(latex_output)
    print(f"✓ LaTeX saved to: {latex_path}")
    
    # Generate HTML
    print(f"\n=== Generating HTML ===")
    html_output = render_template('cv_template.html', filtered_data)
    print(f"✓ HTML template rendered ({len(html_output)} characters)")
    
    # Save HTML file
    html_filename = f"test_cv_{create_filename(test_data['personal_info']['full_name'])}.html"
    html_path = f"generated/{html_filename}"
    
    with open(html_path, 'w') as f:
        f.write(html_output)
    print(f"✓ HTML saved to: {html_path}")
    
    # Generate PDF
    print(f"\n=== Generating PDF ===")
    try:
        # Use pdflatex to generate PDF
        result = subprocess.run([
            "pdflatex", 
            "-output-directory=generated", 
            "-interaction=nonstopmode",  # Don't stop for errors
            latex_path
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            pdf_filename = latex_filename.replace('.tex', '.pdf')
            pdf_path = f"generated/{pdf_filename}"
            
            if os.path.exists(pdf_path):
                print(f"✓ PDF generated successfully: {pdf_path}")
                
                # Get file size
                file_size = os.path.getsize(pdf_path)
                print(f"  PDF size: {file_size:,} bytes")
            else:
                print(f"⚠ PDF file not found after compilation")
        else:
            print(f"⚠ PDF generation failed with return code: {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr}")
            if result.stdout:
                # Show last few lines of output for debugging
                lines = result.stdout.strip().split('\n')
                print(f"  Last output lines:")
                for line in lines[-5:]:
                    print(f"    {line}")
                    
    except FileNotFoundError:
        print(f"⚠ pdflatex not found. Please install a LaTeX distribution (e.g., MacTeX, MikTeX)")
    except Exception as e:
        print(f"⚠ Error generating PDF: {e}")
    
    # Content validation
    print(f"\n=== Content Validation ===")
    
    # Check LaTeX content
    name = test_data['personal_info']['full_name']
    if name in latex_output:
        print("✓ Personal info rendered in LaTeX")
    
    if "Stanford University" in latex_output:
        print("✓ Education section rendered in LaTeX")
    
    if "Dean's List" in latex_output:
        print("✓ Achievements section rendered in LaTeX")
    
    if "Google" in latex_output:
        print("✓ Internships section rendered in LaTeX")
    
    if "AI-Powered Code Review" in latex_output:
        print("✓ Projects section rendered in LaTeX")
    
    if "Computer Science Society" in latex_output:
        print("✓ Positions of Responsibility rendered in LaTeX")
    
    if "Marathon running" in latex_output:
        print("✓ Extracurricular activities rendered in LaTeX")
    
    if "Python" in latex_output and "JavaScript" in latex_output:
        print("✓ Technical skills rendered in LaTeX")
    
    # Check HTML content
    if name in html_output:
        print("✓ Personal info rendered in HTML")
    
    # Check for LaTeX syntax issues
    if "{{" in latex_output:
        print("⚠ Warning: Found unreplaced Jinja2 variables in LaTeX")
    else:
        print("✓ No unreplaced variables in LaTeX")
    
    if "{{" in html_output:
        print("⚠ Warning: Found unreplaced Jinja2 variables in HTML")
    else:
        print("✓ No unreplaced variables in HTML")
    
    print(f"\n=== Test Summary ===")
    print(f"LaTeX file: {latex_path}")
    print(f"HTML file: {html_path}")
    
    if os.path.exists(f"generated/{latex_filename.replace('.tex', '.pdf')}"):
        print(f"PDF file: generated/{latex_filename.replace('.tex', '.pdf')}")
    
    print(f"\n=== Sample LaTeX Output (Education Section) ===")
    lines = latex_output.split('\n')
    for i, line in enumerate(lines):
        if 'Educational Qualifications' in line:
            print(f"Education section starts at line {i+1}:")
            for j in range(max(0, i-1), min(len(lines), i+15)):
                print(f"{j+1:3}: {lines[j]}")
            break
    
    print(f"\n=== Test Complete ===")
    return {
        'latex_output': latex_output,
        'html_output': html_output,
        'latex_path': latex_path,
        'html_path': html_path
    }

if __name__ == "__main__":
    test_template_system()