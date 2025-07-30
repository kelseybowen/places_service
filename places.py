import os
from dotenv import load_dotenv
import requests
import json
import zmq

load_dotenv()

API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5556")


def find_places(query):    
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.id'
    }
    data = {
        'textQuery': query
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Response 200")
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return json.loads(response.text)

# Function based on code provided by Gemini:
def get_place_details(place_ids, api_key):
    base_url = "https://places.googleapis.com/v1/places/"
    place_details_list = []
    for place_id in place_ids:
        place_name = None
        place_description = None
        place_types = None
        # --- Attempt 1: Fetch with generativeSummary.overview and types ---
        fields_attempt1 = "id,displayName.text,types,generativeSummary.overview"
        url_attempt1 = f"{base_url}{place_id}?fields={fields_attempt1}"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": fields_attempt1
        }
        response_attempt1 = requests.get(url_attempt1, headers=headers)
        place_data_attempt1 = response_attempt1.json()
        place_name = place_data_attempt1.get('displayName', {}).get('text')
        place_types = place_data_attempt1.get('types')
        place_description = place_data_attempt1.get('generativeSummary', {}).get('overview')
        # If generativeSummary is not available, try editorialSummary
        if not place_description:
            fields_attempt2 = "id,displayName.text,types,editorialSummary.overview"
            url_attempt2 = f"{base_url}{place_id}?fields={fields_attempt2}"
            headers["X-Goog-FieldMask"] = fields_attempt2
            
            response_attempt2 = requests.get(url_attempt2, headers=headers)
            place_data_attempt2 = response_attempt2.json()
            # Re-get name and types in case the first attempt failed completely
            place_name = place_data_attempt2.get('displayName', {}).get('text')
            place_types = place_data_attempt2.get('types')
            place_description = place_data_attempt2.get('editorialSummary', {}).get('overview')
        place_details_list.append({
            'id': place_id,
            'name': place_name,
            'types': place_types,
            'description': place_description
        })
    return place_details_list

while True:
    message = socket.recv()
    search_criteria = message.decode()
    place_ids = find_places(search_criteria)
    my_place_ids = [place_ids['places'][i]['id'] for i in range(len(place_ids['places']))]
    details = get_place_details(my_place_ids, API_KEY)
    json_data = json.dumps(details)
    socket.send_string(json_data)
    print(f"Data sent to main program: {json_data}")

context.destroy()

