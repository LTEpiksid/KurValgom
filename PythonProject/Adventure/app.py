import logging
from flask import Flask, render_template_string, jsonify, send_from_directory, request
import folium
import webbrowser
import threading
import asyncio
import aiohttp
from search import search_random_restaurant, search_nearby_restaurants
from get_info import get_restaurant_info

app = Flask(__name__, static_url_path='/static')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

@app.route('/static/<path:filename>')
def send_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
<html>
<head>
    <title>KurValgom?</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Meow+Script&display=swap');
        body {
            font-family: Arial, sans-serif;
            background-color: #1e122b;
            margin: 0;
            padding: 20px;
        }
        .banner {
            background-color: #ADDFAD;
            color: black;
            text-align: center;
            padding: 12px 12px;
            font-size: 50px;
            font-family: 'Meow Script', cursive;
            font-weight: bold;
            border: 10px solid #ffc466;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .logo {
            height: 50px;
            margin-left: 10px;
        }
        .content {
            display: flex;
            flex-direction: row;
            justify-content: space-between;
            margin-top: 20px;
        }
        .image-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            margin-right: 20px;
            position: relative;
            width: 50%;
        }
        .slider {
            position: relative;
            width: 100%;
            height: 200px;
        }
        .slider img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 5px;
        }
        .prev, .next {
            cursor: pointer;
            position: absolute;
            top: 50%;
            width: auto;
            margin-top: -22px;
            padding: 16px;
            color: white;
            font-weight: bold;
            font-size: 18px;
            transition: 0.6s ease;
            border-radius: 0 3px 3px 0;
            user-select: none;
            background-color: rgba(0, 0, 0, 0.5);
        }
        .next {
            right: 0;
            border-radius: 3px 0 0 3px;
        }
        .prev:hover, .next:hover {
            background-color: rgba(0, 0, 0, 0.8);
        }
        .description-box {
            width: 100%;
            background-color: #ADDFAD;
            border: 10px solid #ffc466;
            padding: 20px;
            border-radius: 5px;
            color: black;
            margin-top: 20px;
        }
        .generate-container {
            text-align: right;
            flex: 1;
            margin-left: 50px;
            margin-bottom: 20px;
            margin-right: 50px;
        }
        .button {
            padding: 10px 20px;
            font-size: 16px;
            color: black;
            background-color: #ffc466;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }
        .button:hover {
            background-color: #e6ae4e;
        }
        .button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .loading-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        #map-container {
            width: 65%;
            margin-top: 0;
            margin-left: 60px;
        }
        #map {
            width: 100%;
            height: 100%;
            border: 10px solid #ffc466;
            border-radius: 5px;
        }
        h3 {
            color: #333;
            text-align: center;
        }
        #description {
            font-size: 16px;
            color: black;
        }
        #menuContainer {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: left;
        }
        .menu-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 10px;
            border: 2px solid black;
            padding: 10px;
            border-radius: 5px;
            background: url("{{ url_for('static', filename='meniu.jpg') }}") no-repeat center center;
            background-size: cover;
            width: 210px;
            height: 297px;
            overflow: hidden;
            box-sizing: border-box;
        }
        .hidden {
            display: none;
        }
    </style>
    <script>
        let currentSlide = 0;
        let images = [];

        function fetchRestaurant() {
            const button = document.getElementById('generateButton');
            const loadingText = document.getElementById('loadingText');
            const radius = document.getElementById('radiusSelect').value;
            button.disabled = true;
            loadingText.style.display = 'block';

            navigator.geolocation.getCurrentPosition(position => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                fetch(`/random_restaurant?lat=${lat}&lon=${lon}&radius=${radius}`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('map').innerHTML = data.map_html;
                        document.getElementById('description').innerText = data.description;
                        document.getElementById('restaurantName').innerText = data.name;
                        document.getElementById('location').innerText = "Location: " + data.location;
                        document.getElementById('rating').innerText = "Rating: " + data.rating;

                        images = data.image_urls;
                        currentSlide = 0;
                        showSlide(currentSlide);

                        const menuContainer = document.getElementById('menuContainer');
                        menuContainer.innerHTML = '';
                        data.menu_pdfs.forEach(pdf => {
                            const menuBox = document.createElement('div');
                            menuBox.className = 'menu-box';
                            menuBox.onclick = () => window.open(pdf, '_blank');
                            menuContainer.appendChild(menuBox);
                        });

                        document.querySelectorAll('.hidden').forEach(el => el.style.display = 'block');
                    })
                    .finally(() => {
                        button.disabled = false;
                        loadingText.style.display = 'none';
                    });
            }, error => {
                alert('Failed to get your location. Please try again.');
                button.disabled = false;
                loadingText.style.display = 'none';
            });
        }

        function showSlide(index) {
            const img = document.getElementById('slideImg');
            img.src = images[index];
        }

        function nextSlide() {
            currentSlide = (currentSlide + 1) % images.length;
            showSlide(currentSlide);
        }

        function prevSlide() {
            currentSlide = (currentSlide - 1 + images.length) % images.length;
            showSlide(currentSlide);
        }

        function closeModal() {
            document.getElementById('myModal').style.display = 'none';
        }
    </script>
</head>
<body>
    <div class="banner">
        KurValgom?
        <img src="{{ url_for('static', filename='logo.jpg') }}" alt="Logo" class="logo">
    </div>
    <div class="content">
        <div class="generate-container">
            <select id="radiusSelect" class="button">
                <option value="2000">2 km</option>
                <option value="5000">5 km</option>
                <option value="10000">10 km</option>
                                <option value="15000">15 km</option>
                <option value="vilnius">Vilnius</option>
            </select>
            <button id="generateButton" class="button" onclick="fetchRestaurant()">Surasti Restorana</button>
            <div id="loadingText" class="loading-text" style="display:none;">Loading...</div>
        </div>
        <div class="image-container">
            <div class="slider">
                <a class="prev" onclick="prevSlide()">&#10094;</a>
                <img id="slideImg" src="https://via.placeholder.com/300.png?text=Restaurant+Image">
                <a class="next" onclick="nextSlide()">&#10095;</a>
            </div>
            <div class="description-box">
                <h3 id="restaurantName">Restaurant Name</h3>
                <p id="description">No description yet</p>
                <p id="location">Location: Not available</p>
                <p id="rating">Rating: Not available</p> <!-- Added rating -->
            </div>
        </div>
        <div id="map-container">
            <div id="map"></div>
        </div>
    </div>
    <div class="menu-pdfs" id="menuContainer">
        <h3>Restaurant Menu PDFs:</h3>
    </div>
</body>
</html>
    """)

async def fetch_restaurant_data(lat=None, lon=None, radius=None):
    async with aiohttp.ClientSession() as session:
        while True:
            if radius == "vilnius":
                restaurant = search_random_restaurant()
            else:
                restaurant = search_nearby_restaurants(lat, lon, int(radius))

            if restaurant:
                lat = restaurant['lat']
                lon = restaurant['lon']
                name = restaurant['tags'].get('name', 'Unnamed')
                description, image_urls, menu_pdfs, rating = get_restaurant_info(name)  # Receive rating here
                location = f"{lat}, {lon}"

                if description != "No description available":
                    map_ = folium.Map(location=[lat, lon], zoom_start=15)
                    folium.Marker([lat, lon], tooltip=name).add_to(map_)

                    map_html = map_._repr_html_()
                    return {
                        'map_html': map_html,
                        'description': description,
                        'name': name,
                        'location': location,
                        'rating': rating,  # Use dynamic rating
                        'image_urls': image_urls,
                        'menu_pdfs': menu_pdfs
                    }


@app.route('/random_restaurant')
def random_restaurant():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    radius = request.args.get('radius')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(fetch_restaurant_data(lat, lon, radius))
    return jsonify(data)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(debug=True, use_reloader=False)
