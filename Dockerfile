# Dockerfile

# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

# Copy the application code and other necessary files
COPY app/ ./app/
COPY main.py .
COPY requirements.txt .
COPY templates/ ./templates/
COPY test_data_structured.json .

# Install system dependencies for Playwright
RUN yum update -y && \
    yum install -y \
    glib2-devel \
    nss \
    nspr \
    at-spi2-atk \
    atk \
    drm \
    xkeyboard-config \
    xorg-x11-xauth \
    xrandr \
    alsa-lib \
    gtk3 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXScrnSaver \
    libXtst \
    pango \
    xorg-x11-fonts-100dpi \
    xorg-x11-fonts-75dpi \
    xorg-x11-fonts-cyrillic \
    xorg-x11-fonts-misc \
    xorg-x11-fonts-Type1 \
    xorg-x11-utils && \
    yum clean all

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium && \
    playwright install-deps chromium

# Set the command to run when the container starts.
# This tells Lambda to use the "handler" object in our "main.py" file.
CMD ["main.handler"]