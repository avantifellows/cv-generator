Tools used - Python FastAPI, Google Sheets API, pandoc for LaTeX to PDF, Amazon SES to send emails

Step 1 - Define a function named readSheetData which
    a. includes OAuth Client ID which grants access to the data of a specified Google Sheet
    b. reads the last row from the Google Sheet and returns the data as a JSON object with key names as column headers. 

Step 2 - Define a function named data_to_tex which 
    a. creates a copy of the 1pg_CV.tex file 
    b. calls the readSheetData function
    c. passes the data from the readSheetData function to the corresponding variables in the .tex copy
    d. returns the modified template as a temporary .tex file

Step 3 - Define a function named tex_to_pdf which converts modified temp .tex file to .pdf and returns the .pdf file

Step 4 - Define a function named email_cv which
    a. gets email data from the readSheetData function
    b. includes OAuth Client ID which grants access to compose and send emails from the admin's email ID
    b. uses GMail API to compose a standard email body, attaches the pdf file from the tex_to_pdf function and sends the email to the address collected from the readSheetData function

Step 5 - Define a function to handle errors and edge cases

Step 6 - Create a console logger to track errors in each function

Step 7 - Define a function called cv_generator which 
    a. creates a trigger which is activated when a new row is added to a specified Google Sheet
    b. calls the functions defined above sequentially
    c. deletes any temp files created in the process

