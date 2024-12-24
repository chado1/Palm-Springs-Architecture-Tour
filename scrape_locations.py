import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import quote
import re

def get_coordinates(address):
    """Get coordinates for an address using Nominatim."""
    base_url = "https://nominatim.openstreetmap.org/search"
    # Add Palm Springs, CA to make the search more accurate
    full_address = f"{address}, Palm Springs, CA"
    params = {
        'q': full_address,
        'format': 'json',
        'limit': 1
    }
    
    # Add user agent to comply with Nominatim's terms of service
    headers = {
        'User-Agent': 'PalmSpringsArchitectureTour/1.0'
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()
        
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
        return None
    except Exception as e:
        print(f"Error geocoding {address}: {str(e)}")
        return None

def extract_address(text):
    """Extract address from text using common patterns."""
    # Common address patterns
    patterns = [
        r'\d+\s+(?:North|South|East|West|N\.|S\.|E\.|W\.)\s+[A-Za-z\s]+(?:Street|St\.|Drive|Dr\.|Road|Rd\.|Avenue|Ave\.|Boulevard|Blvd\.|Way|Circle|Cir\.|Place|Pl\.|Court|Ct\.)',
        r'\d+\s+[A-Za-z\s]+(?:Street|St\.|Drive|Dr\.|Road|Rd\.|Avenue|Ave\.|Boulevard|Blvd\.|Way|Circle|Cir\.|Place|Pl\.|Court|Ct\.)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

def clean_text(text):
    """Clean and normalize text."""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove special characters except basic punctuation
    text = re.sub(r'[^\w\s\-\.,]', '', text)
    return text

def scrape_locations():
    url = "https://visitpalmsprings.com/mid-century-architecture-self-guided-tour/"
    
    try:
        print("Fetching webpage...")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        locations = []
        seen_addresses = set()  # To avoid duplicates
        
        # Find all text blocks that might contain addresses
        content_elements = soup.find_all(['p', 'div', 'li'])
        
        print("Extracting locations...")
        for element in content_elements:
            text = clean_text(element.get_text().strip())
            
            # Skip empty or very short texts
            if len(text) < 10:
                continue
                
            # Try to extract address
            address = extract_address(text)
            if address and address not in seen_addresses:
                seen_addresses.add(address)
                
                # Get description (text before and after address)
                full_text = text
                description = full_text.replace(address, '').strip()
                
                print(f"Found address: {address}")
                
                # Get coordinates
                coords = get_coordinates(address)
                if coords:
                    lat, lng = coords
                    locations.append({
                        "name": "",  # We can add name extraction later if needed
                        "address": address,
                        "lat": lat,
                        "lng": lng,
                        "description": description
                    })
                    print(f"Got coordinates for {address}: ({lat}, {lng})")
                    # Sleep to respect Nominatim's rate limit
                    time.sleep(1)
                else:
                    print(f"Could not get coordinates for {address}")
        
        # Save to JSON file
        with open('data/locations.json', 'w') as f:
            json.dump(locations, f, indent=4)
        
        print(f"\nSuccessfully scraped {len(locations)} locations")
        print("Locations saved to data/locations.json")
        
    except Exception as e:
        print(f"Error scraping locations: {str(e)}")

if __name__ == "__main__":
    scrape_locations()
