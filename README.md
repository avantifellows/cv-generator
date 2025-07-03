# CV Generator

A modern FastAPI web application that generates professional PDF and HTML resumes from dynamic LaTeX templates with conditional rendering.

## Features

- **Dynamic Content Rendering**: Only shows sections with actual content (no empty bullet points or sections)
- **Web-based Form**: Easy-to-use interface for entering CV information
- **Dual Output**: Generates both PDF and HTML versions of your CV
- **Conditional Templates**: Smart Jinja2 templates that adapt based on your data
- **Structured Data Storage**: Saves complete CV data in JSON format for future editing
- **Professional Formatting**: Clean, academic-style LaTeX output
- **Built with FastAPI**: Modern, fast Python web framework

## Prerequisites

- Python 3.7+
- LaTeX distribution with pdflatex
- Virtual environment (recommended)

### Installing LaTeX

**macOS:**
```bash
brew install --cask mactex
```

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended
```

**Windows:**
Download MikTeX from https://miktex.org/download

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd cv-generator
```

2. Create a virtual environment:
```bash
python3 -m venv env
```

3. Activate the virtual environment:
```bash
# On macOS/Linux:
source env/bin/activate

# On Windows:
env\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Activate the virtual environment (if not already activated):
```bash
source env/bin/activate
```

2. Start the server:
```bash
python main.py
```

Alternatively, you can use uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

1. **Fill out the CV form** with your information at `http://localhost:8000`
2. **Submit the form** to generate your CV with a unique ID
3. **View the HTML version** or **download the PDF** directly from the results page
4. **Only filled sections appear** - empty optional fields are automatically hidden

### Smart Content Rendering

The application intelligently renders your CV:
- ✅ **Education entries**: Only shows rows with actual qualifications
- ✅ **Achievements**: Hidden if no achievements are entered
- ✅ **Internships**: Only appears if you have internship experience
- ✅ **Projects**: Hidden if no projects are entered
- ✅ **Positions of Responsibility**: Only shows if you have leadership roles
- ✅ **Extracurricular Activities**: Hidden if no activities are listed
- ✅ **Technical Skills**: Only shows filled skill entries

## Testing

### Quick Test with Sample Data

Run the comprehensive test script to validate the template system:

```bash
# Activate virtual environment
source env/bin/activate

# Run the test script
python test_template.py
```

This will:
- Load realistic sample data from `test_data.json`
- Generate LaTeX, HTML, and PDF files
- Validate all sections render correctly
- Check for template syntax errors
- Output files: `generated/test_cv_jane_smith.*`

### Manual Testing

1. **Start the server**:
   ```bash
   source env/bin/activate
   python main.py
   ```

2. **Test different scenarios**:
   - Fill all fields to test complete CV generation
   - Leave some sections empty to test conditional rendering
   - Try various combinations of filled/empty fields

3. **Verify outputs**:
   - Check HTML version displays correctly
   - Ensure PDF downloads with proper filename
   - Confirm empty sections don't appear

### Test Files Generated

- `generated/test_cv_jane_smith.tex` - LaTeX source
- `generated/test_cv_jane_smith.html` - HTML version
- `generated/test_cv_jane_smith.pdf` - PDF output
- `test_data.json` - Sample CV data for testing

## Project Structure

```
cv-generator/
├── main.py                 # FastAPI application with conditional rendering
├── requirements.txt        # Python dependencies
├── test_template.py        # Comprehensive test script
├── test_data.json         # Sample CV data for testing
├── templates/
│   ├── form.html          # Web form for CV input
│   ├── cv_template.tex    # Jinja2 LaTeX template with conditionals
│   └── cv_template.html   # Jinja2 HTML template with conditionals
├── generated/             # Generated CV files (LaTeX, HTML, PDF, JSON)
├── static/               # Static web assets
└── env/                  # Virtual environment
```

## API Endpoints

- `GET /` - CV form page
- `POST /generate` - Generate CV from form data (returns redirect to CV page)
- `GET /cv/{cv_id}` - View generated CV with download button
- `GET /cv/{cv_id}/html` - Download raw HTML CV
- `GET /cv/{cv_id}/pdf` - Download PDF CV with custom filename

## Technical Details

### Template System

The application uses **Jinja2 templates** for both LaTeX and HTML generation:

- **Conditional Rendering**: Sections only appear if they contain data
- **Smart Filtering**: Empty entries are automatically removed
- **Professional Formatting**: Clean LaTeX output without syntax errors
- **Responsive Design**: HTML version works on all devices

### Data Storage

Each generated CV includes:
- **LaTeX source** (`{cv_id}.tex`)
- **HTML version** (`{cv_id}.html`)  
- **PDF output** (`{cv_id}.pdf`)
- **Structured JSON data** (`{cv_id}_data.json`) for future editing
- **Display HTML** (`{cv_id}_display.html`) with download button

### File Naming

PDFs are automatically named using the person's name:
- Input: "Jane Smith" → Output: `jane_smith.pdf`
- Handles special characters and spaces automatically

## Troubleshooting

### Common Issues

#### LaTeX Installation
If you get `pdflatex not found` errors:
```bash
# Check if pdflatex is installed
which pdflatex

# If not found, install LaTeX:
# macOS:
brew install --cask mactex

# Ubuntu/Debian:
sudo apt-get install texlive-latex-recommended
```

#### PDF Generation Stops with Questions
If pdflatex asks questions during compilation, restart the server to load template fixes:
```bash
# Stop server (Ctrl+C), then restart:
source env/bin/activate
python main.py
```

#### Template Syntax Errors
Run the test script to validate templates:
```bash
python test_template.py
```

#### Port Already in Use
If port 8000 is busy:
```bash
# Use a different port
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Getting Help

- Check the `generated/` folder for LaTeX error files (`.log`)
- Run `python test_template.py` to validate the system
- Ensure all dependencies are installed
- Restart the server after making template changes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `python test_template.py`
4. Submit a pull request

## License

This project is open source. Feel free to use and modify as needed.