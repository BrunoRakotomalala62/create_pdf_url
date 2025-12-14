from flask import Flask, request, Response, jsonify
import requests
import re
from playwright.sync_api import sync_playwright
import json
from io import BytesIO
import img2pdf
from PIL import Image
import tempfile
import os

app = Flask(__name__)

def get_chromium_path():
    possible_paths = [
        '/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/opt/render/.cache/ms-playwright/chromium-*/chrome-linux/chrome',
    ]
    
    import glob
    for path in possible_paths:
        if '*' in path:
            matches = glob.glob(path)
            if matches:
                return matches[0]
        elif os.path.exists(path):
            return path
    return None

def download_image(url, headers):
    """Download an image from URL"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.content
    except:
        return None

def images_to_pdf(image_data_list):
    """Convert list of image bytes to PDF"""
    try:
        temp_files = []
        for i, img_data in enumerate(image_data_list):
            img = Image.open(BytesIO(img_data))
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            temp_path = f"/tmp/page_{i}.jpg"
            img.save(temp_path, 'JPEG', quality=95)
            temp_files.append(temp_path)
        
        pdf_bytes = img2pdf.convert(temp_files)
        
        for f in temp_files:
            try:
                os.remove(f)
            except:
                pass
        
        return pdf_bytes
    except Exception as e:
        return None

def get_pdf_from_papermark(url, email="user@download.com"):
    """Extract and download PDF from Papermark URL using Playwright"""
    pdf_urls = []
    image_urls = []
    all_urls = []
    pdf_content = None
    document_name = "document"
    
    try:
        with sync_playwright() as p:
            chromium_path = get_chromium_path()
            launch_args = {
                'headless': True,
                'args': ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--headless=new']
            }
            if chromium_path:
                launch_args['executable_path'] = chromium_path
            
            browser = p.chromium.launch(**launch_args)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            def handle_response(response):
                resp_url = response.url
                all_urls.append(resp_url)
                content_type = response.headers.get('content-type', '')
                if 'pdf' in content_type.lower():
                    pdf_urls.append(resp_url)
                if 'cloudfront' in resp_url and 'page-' in resp_url and '.png' in resp_url:
                    image_urls.append(resp_url)
            
            page.on('response', handle_response)
            
            page.goto(url, wait_until='networkidle', timeout=45000)
            page.wait_for_timeout(2000)
            
            next_data = page.query_selector('#__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.inner_text())
                    doc_name = data.get('props', {}).get('pageProps', {}).get('linkData', {}).get('link', {}).get('document', {}).get('name', '')
                    if doc_name:
                        document_name = doc_name.replace('.pdf', '')
                except:
                    pass
            
            try:
                email_input = page.query_selector('input[type="email"]')
                if not email_input:
                    email_input = page.query_selector('input[placeholder*="email" i]')
                
                if email_input:
                    email_input.fill(email)
                    page.wait_for_timeout(500)
                    
                    submit_button = page.query_selector('button[type="submit"]')
                    if not submit_button:
                        submit_button = page.query_selector('button:has-text("Continue")')
                    if not submit_button:
                        submit_button = page.query_selector('button:has-text("Access")')
                    
                    if submit_button:
                        submit_button.click()
                        page.wait_for_load_state('networkidle', timeout=30000)
                        page.wait_for_timeout(5000)
            except:
                pass
            
            browser.close()
        
        sorted_images = sorted(set(image_urls), key=lambda x: int(re.search(r'page-(\d+)', x).group(1)) if re.search(r'page-(\d+)', x) else 0)
        
        if sorted_images:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            image_data_list = []
            for img_url in sorted_images:
                img_data = download_image(img_url, headers)
                if img_data:
                    image_data_list.append(img_data)
            
            if image_data_list:
                pdf_bytes = images_to_pdf(image_data_list)
                if pdf_bytes:
                    return pdf_bytes, None, document_name
        
        pdf_url = None
        for u in pdf_urls:
            if '.pdf' in u.lower():
                pdf_url = u
                break
        
        if pdf_url:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            pdf_response = requests.get(pdf_url, headers=headers, timeout=60)
            pdf_response.raise_for_status()
            
            if pdf_response.content[:4] == b'%PDF':
                return pdf_response.content, None, document_name
        
        return None, f"Could not find PDF or images to download. The document may be protected.", document_name
        
    except Exception as e:
        return None, f"Error: {str(e)}", document_name

@app.route('/')
def index():
    return jsonify({
        "message": "PDF Download API for Papermark",
        "endpoints": {
            "/info": {
                "method": "GET",
                "description": "Get PDF name and dynamic download URL",
                "parameters": {
                    "pdf": "Papermark URL (required)",
                    "email": "Your email (optional, default: monsieurbruno0@gmail.com)"
                },
                "example": "/info?pdf=https://www.papermark.com/view/cmj45iz65000el804x9fkmzg7"
            },
            "/download": {
                "method": "GET",
                "description": "Download the PDF directly",
                "parameters": {
                    "pdf": "Papermark URL (required)",
                    "email": "Your email (optional)"
                },
                "example": "/download?pdf=https://www.papermark.com/view/cmj45iz65000el804x9fkmzg7&email=user@example.com"
            }
        },
        "note": "This API converts Papermark document images into a downloadable PDF."
    })

@app.route('/recherche')
def recherche_pdf():
    search_term = request.args.get('pdf', '')
    
    if not search_term:
        return jsonify({"error": "Missing 'pdf' parameter"}), 400
    
    try:
        with open('cache_url_json.json', 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "Cache file not found"}), 500
    
    search_words = search_term.lower().split()
    
    results = []
    for pdf_entry in cache_data.get('pdfs', []):
        nom_lower = pdf_entry.get('nom', '').lower()
        if any(word in nom_lower for word in search_words):
            url_papermark = pdf_entry.get('url_papermark', '')
            
            from urllib.parse import quote
            base_url = request.host_url.rstrip('/')
            email = 'monsieurbruno0@gmail.com'
            download_url = f"{base_url}/download?pdf={quote(url_papermark, safe='')}&email={quote(email, safe='')}"
            
            results.append({
                "titre": pdf_entry.get('nom'),
                "url_telechargement": download_url
            })
    
    if not results:
        return jsonify({"error": f"No PDF found matching '{search_term}'"}), 404
    
    if len(results) == 1:
        return jsonify(results[0])
    
    return jsonify({"resultats": results})

@app.route('/info')
def pdf_info():
    pdf_url = request.args.get('pdf')
    email = request.args.get('email', 'monsieurbruno0@gmail.com')
    
    if not pdf_url:
        return jsonify({"error": "Missing 'pdf' parameter"}), 400
    
    if 'papermark.com' not in pdf_url:
        return jsonify({"error": "URL must be from papermark.com"}), 400
    
    document_name = "document"
    
    try:
        with sync_playwright() as p:
            chromium_path = get_chromium_path()
            launch_args = {
                'headless': True,
                'args': ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--headless=new']
            }
            if chromium_path:
                launch_args['executable_path'] = chromium_path
            
            browser = p.chromium.launch(**launch_args)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            page.goto(pdf_url, wait_until='networkidle', timeout=45000)
            page.wait_for_timeout(2000)
            
            next_data = page.query_selector('#__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.inner_text())
                    doc_name = data.get('props', {}).get('pageProps', {}).get('linkData', {}).get('link', {}).get('document', {}).get('name', '')
                    if doc_name:
                        document_name = doc_name.replace('.pdf', '')
                except:
                    pass
            
            browser.close()
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500
    
    from urllib.parse import quote
    base_url = request.host_url.rstrip('/')
    download_url = f"{base_url}/download?pdf={quote(pdf_url, safe='')}&email={quote(email, safe='')}"
    
    return jsonify({
        "titre": document_name,
        "url_telechargement": download_url
    })

@app.route('/download')
def download_pdf():
    pdf_url = request.args.get('pdf')
    email = request.args.get('email', 'monsieurbruno0@gmail.com')
    
    if not pdf_url:
        return jsonify({"error": "Missing 'pdf' parameter"}), 400
    
    if 'papermark.com' not in pdf_url:
        return jsonify({"error": "URL must be from papermark.com"}), 400
    
    pdf_content, error, doc_name = get_pdf_from_papermark(pdf_url, email)
    
    if error:
        return jsonify({"error": error}), 500
    
    filename = f"{doc_name}.pdf"
    
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
