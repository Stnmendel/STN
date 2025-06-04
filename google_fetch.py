import os
import googlemaps

from datetime import datetime
from typing import List, Dict

# Set your Google Maps API key in the environment variable GOOGLE_API_KEY
API_KEY = os.getenv('GOOGLE_API_KEY')

if not API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY environment variable not set")

# Initialize the Google Maps client
client = googlemaps.Client(key=API_KEY)

def fetch_businesses(query: str, location: str = None, radius: int = 5000) -> List[Dict]:
    """Fetch businesses from Google Places by search query."""
    params = {
        'query': query,
        'type': 'establishment'
    }
    if location:
        params['location'] = location
        params['radius'] = radius
    results = client.places(**params)
    businesses = []
    for place in results.get('results', []):
        place_id = place['place_id']
        details = client.place(place_id=place_id, fields=['name', 'formatted_address',
                                                         'formatted_phone_number',
                                                         'website', 'review'])
        info = details.get('result', {})
        name = info.get('name')
        address = info.get('formatted_address')
        phone = info.get('formatted_phone_number')
        website = info.get('website')
        reviews = info.get('reviews', [])
        comments = [r.get('text', '') for r in reviews]
        businesses.append({
            'name': name,
            'address': address,
            'phone': phone,
            'website': website,
            'comments': comments,
        })
    return businesses

def summarize_comments(comments: List[str]) -> str:
    """Simple AI-like summary of comments using a naive approach."""
    if not comments:
        return "No comments available."
    # Basic frequency-based summarization as a placeholder
    from collections import Counter
    words = ' '.join(comments).split()
    common = Counter(words).most_common(5)
    summary = ' '.join([w for w, _ in common])
    return f"Summary of comments: {summary}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fetch businesses from Google Places')
    parser.add_argument('query', help='Search query or category (e.g., "restaurants")')
    parser.add_argument('--location', help='Location as "lat,lng" (optional)')
    parser.add_argument('--radius', type=int, default=5000, help='Search radius in meters')
    args = parser.parse_args()

    businesses = fetch_businesses(args.query, args.location, args.radius)
    for biz in businesses:
        summary = summarize_comments(biz['comments'])
        print('---')
        print('Name:', biz['name'])
        print('Address:', biz['address'])
        print('Phone:', biz['phone'])
        print('Website:', biz['website'])
        print(summary)

if __name__ == '__main__':
    main()
