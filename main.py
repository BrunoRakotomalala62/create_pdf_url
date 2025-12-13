from flask import Flask, request, Response, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def get_pdf_from_papermark(url):
    """Extract and download PDF from Papermark URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        pdf_url = None
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                pdf_match = re.search(r'https?://[^\s"\'<>]+\.pdf[^\s"\'<>]*', script.string)
                if pdf_match:
                    pdf_url = pdf_match.group(0)
                    break
        
        if not pdf_url:
            for tag in soup.find_all(['a', 'embed', 'object', 'iframe']):
                href = tag.get('href') or tag.get('src') or tag.get('data')
                if href and '.pdf' in href.lower():
                    pdf_url = href
                    break
        
        if not pdf_url:
            json_match = re.search(r'"file":\s*"([^"]+\.pdf[^"]*)"', response.text)
            if json_match:
                pdf_url = json_match.group(1)
        
        if not pdf_url:
            json_match = re.search(r'"url":\s*"([^"]+\.pdf[^"]*)"', response.text)
            if json_match:
                pdf_url = json_match.group(1)
        
        if not pdf_url:
            return None, "Could not find PDF URL in the Papermark page"
        
        pdf_response = requests.get(pdf_url, headers=headers, timeout=60)
        pdf_response.raise_for_status()
        
        return pdf_response.content, None
        
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

@app.route('/')
def index():
    return jsonify({
        "message": "PDF Download API",
        "usage": "GET /download?pdf=<papermark_url>",
        "example": "/download?pdf=https://www.papermark.com/view/cmj45iz65000el804x9fkmzg7"
    })

@app.route('/download')
def download_pdf():
    pdf_url = request.args.get('pdf')
    
    if not pdf_url:
        return jsonify({"error": "Missing 'pdf' parameter"}), 400
    
    if 'papermark.com' not in pdf_url:
        return jsonify({"error": "URL must be from papermark.com"}), 400
    
    pdf_content, error = get_pdf_from_papermark(pdf_url)
    
    if error:
        return jsonify({"error": error}), 500
    
    view_id = pdf_url.split('/')[-1]
    filename = f"document_{view_id}.pdf"
    
    return Response(
        pdf_content,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'application/pdf'
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
