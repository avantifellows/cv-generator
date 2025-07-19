# Dockerfile

# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies
RUN yum install -y \
    pango \
    pango-devel \
    cairo \
    gdk-pixbuf2 \
    libffi \
    libxml2 \
    libxslt \
    freetype \
    fontconfig \
    harfbuzz \
    fribidi \
    glib2 \
    libpng \
    libjpeg-turbo \
    && yum clean all \
    && ln -sf /usr/lib64/libpango-1.0.so.0 /usr/lib64/libpango-1.0-0 \
    && ln -sf /usr/lib64/libpango-1.0.so.0 /usr/lib/libpango-1.0-0 || true

# Copy the application code and other necessary files
COPY app/ ./app/
COPY main.py .
COPY requirements.txt .
COPY templates/ ./templates/
COPY test_data_structured.json .

#COPY . ${LAMBDA_TASK_ROOT}

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV LD_LIBRARY_PATH=/usr/lib64:/usr/lib:/lib:/var/lang/lib

# Set the command to run when the container starts.
# This tells Lambda to use the "handler" object in our "main.py" file.
CMD ["main.handler"]