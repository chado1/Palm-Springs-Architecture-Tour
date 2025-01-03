# Palm Springs Mid-Century Modern Architecture Walking Tour

A web application that provides optimized walking routes for exploring Palm Springs' famous mid-century modern architecture. The app creates multiple loops of reasonable walking distance, making it easy to explore the city's architectural heritage at your own pace.

## Features
- Interactive map showing architectural points of interest
- Multiple color-coded walking loops for manageable distances
- Optimized walking routes between locations
- Detailed information about each building including:
  - Architect and year built
  - Full address with Google Maps integration
  - Historical and architectural significance
- Welcome dialog with usage instructions and GitHub link
- Mobile-friendly interface
- Real-time distance calculations
- Automatic route optimization based on walking distance
- Settings persistence across sessions

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
- Storage: LocalStorage for user preferences

## Features
### Multiple Walking Loops
- Routes are automatically divided into manageable walking loops
- Each loop is color-coded for easy identification
- Markers and route lines share the same color scheme

### Interactive Interface
- Click on any marker to view building information
- Direct links to Google Maps for precise navigation
- Click on list items to pan/zoom to locations
- Collapsible sidebar for better mobile viewing
- Welcome dialog with helpful information

### Route Optimization
- Routes are optimized for walking distance
- Real walking paths using street data
- Automatic route segmentation based on maximum walking distance
- Configurable maximum walking distance
- Support for both metric (km) and imperial (mi) units

### Data Management
- Precise location coordinates
- Detailed architectural information
- Custom Google Maps links for each location
- Persistent user preferences across sessions

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is open source and available under the MIT License.
