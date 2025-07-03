The goal of this project is to present the student with a PDF version of their resume. The app should be based on FastAPI with a simple form frontend to take input from the user.

The output should be a HTML resume with a unique link that can be downloaded as PDF as well. The tool shoudl also take email as input and use Amazon SES to send an email to the user with the PDF link and the link to the HTML resume

# Step 1
1. Create a webform that takes inputs that can fill up the individual sections as defined in 1pg_CV.tex. The form shoudl allow the user to input additional bullet points in the subsections.

# Step 2 
1. When user clicks the Submit button, fill the LaTeX template with these variables, save it as a new file.
2. Use pandoc to generate HTML and PDF versions. 

Let us do this first and later we can add the following features:

1. Emailing the user a PDF copy of their resume
2. Real time preview of the resume
