# PDF Download API

## Overview
A simple Flask API that allows downloading PDFs from Papermark URLs directly to your device.

## Usage
- **Endpoint**: `GET /download?pdf=<papermark_url>`
- **Example**: `/download?pdf=https://www.papermark.com/view/cmj45iz65000el804x9fkmzg7`

## API Endpoints
- `GET /` - API info and usage instructions
- `GET /download?pdf=<url>` - Download PDF from Papermark URL

## Project Structure
- `main.py` - Flask API server
- `requirements.txt` - Python dependencies

## Running
The server runs on port 5000 using Flask.

## Dependencies
- Flask - Web framework
- Requests - HTTP library
- BeautifulSoup4 - HTML parsing
- Gunicorn - Production WSGI server
