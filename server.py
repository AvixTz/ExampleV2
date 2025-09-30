from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os

app = Flask(__name__, static_folder='static')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/extract', methods=['POST'])
def extract_content():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        print(f"Extracting content from: {url}")
        
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title
        title = ''
        title_selectors = ['h1', '.entry-title', '.post-title', '.article-title', 'title']
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                title = element.get_text(strip=True)
                break
        
        # Extract subtitle
        subtitle = ''
        subtitle_selectors = [
            'meta[name="description"]',
            'meta[property="og:description"]',
            '.entry-summary',
            'h2',
            '.subtitle'
        ]
        for selector in subtitle_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    subtitle = element.get('content', '')
                else:
                    subtitle = element.get_text(strip=True)
                if subtitle and subtitle != title:
                    break
        
        # Extract main image
        main_image = ''
        main_image_selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            '.featured-image img',
            '.post-thumbnail img',
            'article img'
        ]
        for selector in main_image_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    main_image = element.get('content', '')
                else:
                    main_image = element.get('src', '') or element.get('data-src', '')
                if main_image:
                    main_image = urljoin(url, main_image)
                    break
        
        # Extract favicon
        favicon = ''
        favicon_element = soup.select_one('link[rel*="icon"]')
        if favicon_element:
            favicon = urljoin(url, favicon_element.get('href', ''))
        
        # Extract ALL images
        all_images = []
        seen_urls = set()
        
        for img in soup.find_all('img'):
            img_src = (
                img.get('src') or 
                img.get('data-src') or 
                img.get('data-lazy-src') or 
                img.get('data-original') or
                ''
            )
            
            if not img_src:
                continue
            
            # Convert to absolute URL
            img_src = urljoin(url, img_src)
            
            # Skip duplicates
            if img_src in seen_urls:
                continue
            seen_urls.add(img_src)
            
            # Filter by size
            width = img.get('width')
            height = img.get('height')
            
            try:
                if width and int(width) < 80:
                    continue
                if height and int(height) < 80:
                    continue
            except:
                pass
            
            # Filter by URL patterns
            if any(pattern in img_src.lower() for pattern in ['icon', 'logo', 'avatar', 'emoji', 'ads', 'banner']):
                # Only skip if size is also small
                if width and height and int(width) < 150 and int(height) < 150:
                    continue
            
            all_images.append(img_src)
        
        # Extract content blocks
        content = []
        content_container = soup.select_one('.entry-content, .post-content, article, .content, .post-body')
        
        if content_container:
            for element in content_container.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'img', 'blockquote'], recursive=True):
                if element.name == 'img':
                    img_src = element.get('src') or element.get('data-src', '')
                    if img_src:
                        img_src = urljoin(url, img_src)
                        content.append({
                            'type': 'image',
                            'content': img_src,
                            'alt': element.get('alt', '')
                        })
                elif element.name in ['h1', 'h2', 'h3', 'h4']:
                    text = element.get_text(strip=True)
                    if len(text) > 10:
                        content.append({
                            'type': 'heading',
                            'content': text,
                            'level': element.name.upper()
                        })
                elif element.name == 'blockquote':
                    text = element.get_text(strip=True)
                    if len(text) > 20:
                        content.append({
                            'type': 'quote',
                            'content': text
                        })
                else:  # paragraph
                    text = element.get_text(strip=True)
                    if len(text) > 30:
                        content.append({
                            'type': 'text',
                            'content': text
                        })
        
        result = {
            'status': 'success',
            'title': title,
            'subtitle': subtitle,
            'mainImage': main_image,
            'favicon': favicon,
            'images': all_images,
            'content': content
        }
        
        print(f"Extracted: {len(all_images)} images, {len(content)} content blocks")
        
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return jsonify({'error': f'Failed to fetch URL: {str(e)}'}), 500
    except Exception as e:
        print(f"Extraction error: {str(e)}")
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 Native Ad Studio Server Started!")
    print("="*60)
    print("\n📱 Open in browser: http://localhost:5000")
    print("\n⚡ Server is running... Press Ctrl+C to stop\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
