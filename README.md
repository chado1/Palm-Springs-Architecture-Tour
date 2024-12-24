# Palm Springs Mid-Century Modern Architecture Walking Tour

A web application that provides optimized walking routes for exploring Palm Springs' famous mid-century modern architecture. The app creates multiple loops of reasonable walking distance, making it easy to explore the city's architectural heritage at your own pace.

## Features
- Interactive map showing architectural points of interest
- Multiple color-coded walking loops for manageable distances
- Optimized walking routes between locations
- Information about each building including its architect, year, and address
- Checklist functionality to track visited locations
- Mobile-friendly interface
- Real-time distance calculations
- Automatic route optimization based on walking distance

## Setup
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to `http://localhost:5000`

## Technology Stack
- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Map: Leaflet.js with OpenStreetMap
- Routing: OSRM (OpenStreetMap Route Machine)
- Data: JSON file containing location information

## Features
### Multiple Walking Loops
- Routes are automatically divided into manageable walking loops
- Each loop is color-coded for easy identification
- Markers and route lines share the same color scheme

### Interactive Interface
- Click on any marker to view building information
- Click on list items to pan/zoom to locations
- Check off buildings as you visit them
- Collapsible sidebar for better mobile viewing

### Route Optimization
- Routes are optimized for walking distance
- Real walking paths using street data
- Automatic route segmentation based on maximum walking distance

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is open source and available under the MIT License.
