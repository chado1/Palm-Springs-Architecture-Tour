# Palm Springs Mid-Century Modern Architecture Tour - Technical Specification

## System Overview
The Palm Springs Architecture Tour is a web application that helps users explore mid-century modern architecture in Palm Springs through optimized walking routes. The application provides an interactive map interface and automatically generates efficient walking tours based on user preferences.

## Core Components

### 1. Web Interface (`templates/index.html`)
- **Purpose**: Provides the main user interface with an interactive map
- **Key Features**:
  - Interactive Leaflet.js map display
  - Collapsible information panel
  - Loading overlay for route calculations
  - Settings panel for route customization
  - Responsive design for mobile and desktop
- **Dependencies**:
  - Leaflet.js (v1.9.4)
  - Leaflet MarkerCluster (v1.4.1)
  - Leaflet.Locate (v0.79.0)
  - Inter font family

### 2. Git Branch Structure
- **Main Branches**:
  - `main`: Production-ready code
  - `develop`: Integration branch for feature development
- **Feature Branches**:
  - `feature/location-updates`: Updates to location data and related functionality
  - `fix/settings-button-hover`: UI fix for settings button hover state
- **Branch Strategy**:
  - Feature branches are created from `develop`
  - Completed features are merged back into `develop`
  - `develop` is merged into `main` for releases
  - Hotfixes can be branched directly from `main`

### 3. Frontend JavaScript Architecture
#### Map Module (`static/js/map.js`)
- **Purpose**: Core map functionality and route display
- **Key Features**:
  - Map initialization and configuration
  - Route visualization
  - Location markers and clustering
  - User location tracking
- **Exposed Global Functions**:
  - `showLoading()`: Display loading overlay
  - `hideLoading()`: Hide loading overlay
  - `loadLocations()`: Load and display route data
- **Global State**:
  - `window.userPreferences`: Stores current route settings

#### Settings Module (`static/js/main.js`)
- **Purpose**: Handles user preferences and settings
- **Key Features**:
  - Settings panel toggle
  - Distance unit conversion (km/mi)
  - Route distance configuration
  - Settings persistence in localStorage
- **Default Settings**:
  - Maximum distance: 5 km
  - Distance unit: kilometers
- **LocalStorage Keys**:
  - `distanceUnit`: User's preferred unit (km/mi)
  - `maxDistance`: Maximum route distance

### 4. Backend Server (`app.py`)
- **Purpose**: Flask server handling route optimization requests
- **Key Features**:
  - Location data caching
  - Route optimization endpoint
  - Error handling and logging
- **Endpoints**:
  - `GET /`: Serves main application page
  - `GET /api/locations`: Returns optimized routes based on parameters
- **Configuration**:
  - Debug mode enabled for development
  - Default port: 5000

### 5. Route Optimizer (`route_optimizer.py`)
- **Purpose**: Core routing logic for creating optimized walking tours
- **Key Features**:
  - Route distance calculation
  - Nearest neighbor pathfinding
  - Integration with OSRM for walking directions
- **Key Functions**:
  - `optimize_route()`: Creates multiple walking loops under specified distance
  - `create_walking_loop()`: Generates single optimized walking route
  - `get_walking_route()`: Fetches walking directions between points
- **Performance Optimizations**:
  - LRU caching for route calculations
  - Fallback to straight-line distance for nearby points (<100m)
  - Candidate filtering using straight-line distance

## Data Structure

### Location Data (`data/locations.json`)
- Format: JSON array of location objects
- Required fields per location:
  - lat: Latitude (float)
  - lng: Longitude (float)
  - name: Location name (string)
  - description: Location details (string)

## Core Functionality Requirements

### 1. Route Optimization
- Preferred walking distance configurable through settings panel (default: 5km)
- Routes may exceed preferred distance when necessary to include all locations
- Distance unit toggleable between kilometers and miles
- Settings persist across sessions using localStorage
- Routes must return to starting point (circular routes)
- Multiple routes generated if locations exceed preferred distance
- Efficient nearest-neighbor pathfinding implementation

### 2. Map Interaction
- Real-time route display
- Location clustering for better visualization
- User location detection capability
- Smooth loading states during calculations

### 3. Settings Management
- Settings changes trigger immediate route recalculation
- Loading state shown during route updates
- Smooth transition between route displays
- Unit conversion handled automatically
- Settings panel toggles without affecting map state

### 4. Error Handling
- Graceful fallback for routing service failures
- Comprehensive error logging
- User-friendly error messages
- Cache management for location data

## Performance Requirements

### Response Times
- Initial page load: < 2 seconds
- Route calculation: < 5 seconds for standard routes
- Map interaction: Real-time response

### Caching
- Location data cached server-side
- Route calculations cached using LRU strategy
- Maximum 1000 cached routes

## External Dependencies

### Routing Service
- OSRM (Open Source Routing Machine)
- Timeout: 2 seconds
- Fallback mechanism for failed requests

### Map Services
- Leaflet.js for map display
- OpenStreetMap for base layer
- MarkerCluster for location grouping

## Security Considerations
- No sensitive data stored or transmitted
- Public API endpoints rate-limited
- Input validation on all parameters
- Secure asset loading (HTTPS)
