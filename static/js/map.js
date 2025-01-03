// Initialize the map centered on Palm Springs
let map;
let markers;
const markerMap = new Map();  // Store markers by location ID

document.addEventListener('DOMContentLoaded', function() {
    // Welcome dialog functionality
    const welcomeDialog = document.getElementById('welcome-dialog');
    const infoButton = document.getElementById('info-button');
    const closeButton = document.getElementById('close-dialog');
    const dontShowCheckbox = document.getElementById('dont-show-again');

    function showDialog() {
        welcomeDialog.style.display = 'flex';
        setTimeout(() => welcomeDialog.classList.add('visible'), 10);
    }

    function hideDialog() {
        welcomeDialog.classList.remove('visible');
        setTimeout(() => welcomeDialog.style.display = 'none', 300);
        
        if (dontShowCheckbox.checked) {
            localStorage.setItem('hideWelcome', 'true');
        }
    }

    // Show welcome dialog on first visit
    if (!localStorage.getItem('hideWelcome')) {
        // Show dialog immediately, don't wait for load
        showDialog();
    }

    // Event listeners for dialog
    infoButton.addEventListener('click', showDialog);
    closeButton.addEventListener('click', () => {
        hideDialog();
        // If the loading is done, remove the loading overlay
        if (!document.getElementById('loading-overlay').style.display || 
            document.getElementById('loading-overlay').style.display === 'none') {
            hideLoading();
        }
    });
    welcomeDialog.addEventListener('click', (e) => {
        if (e.target === welcomeDialog) {
            hideDialog();
            // If the loading is done, remove the loading overlay
            if (!document.getElementById('loading-overlay').style.display || 
                document.getElementById('loading-overlay').style.display === 'none') {
                hideLoading();
            }
        }
    });

    // Initialize map
    map = L.map('map').setView([33.8303, -116.5453], 14);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: ' OpenStreetMap contributors',
        className: 'map-tiles-monochrome' // This class will be used for CSS filters
    }).addTo(map);
    
    // Initialize marker cluster group
    markers = L.markerClusterGroup({
        maxClusterRadius: 40,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        disableClusteringAtZoom: 18,
        iconCreateFunction: function(cluster) {
            const count = cluster.getChildCount();
            return L.divIcon({
                html: `<div><span>${count}</span></div>`,
                className: `marker-cluster marker-cluster-${count < 10 ? 'small' : count < 20 ? 'medium' : 'large'}`,
                iconSize: L.point(40, 40)
            });
        }
    });

    // Add location control
    const locationControl = L.control.locate({
        position: 'topleft',
        strings: {
            title: "Show my location"
        },
        locateOptions: {
            enableHighAccuracy: true,
            maxZoom: 16
        }
    }).addTo(map);

    // Initialize user location marker
    let userMarker = null;
    let userAccuracyCircle = null;

    // User preferences
    const userPreferences = {
        distanceUnit: localStorage.getItem('distanceUnit') || 'mi',
        maxDistance: parseFloat(localStorage.getItem('maxDistance')) || 3.0  // Default to 3 miles
    };

    // Convert distance based on user preference
    function formatDistance(distanceKm) {
        if (userPreferences.distanceUnit === 'mi') {
            return (distanceKm * 0.621371).toFixed(2) + ' miles';
        }
        return distanceKm.toFixed(2) + ' km';
    }

    // Convert distance to kilometers
    function toKilometers(distance, unit) {
        return unit === 'mi' ? distance / 0.621371 : distance;
    }

    // Function to find location by ID
    function findLocationById(locationId) {
        for (const route of window.currentRoutes) {
            for (const location of route.locations) {
                if (location.id === locationId) {
                    return location;
                }
            }
        }
        return null;
    }

    // Function to update the info panel
    function updateInfoPanel(routes) {
        const container = document.getElementById('locations-container');
        container.innerHTML = '';  // Clear existing content
        
        routes.forEach((route, routeIndex) => {
            const routeSection = document.createElement('div');
            routeSection.className = 'route-section';
            const color = routeColors[routeIndex % routeColors.length];
            
            // Add route header
            const routeHeader = document.createElement('div');
            routeHeader.className = 'route-header';
            routeHeader.innerHTML = `
                <h2 style="color: ${color}">Route ${getLoopLetter(routeIndex)}</h2>
                <span class="route-distance" style="color: ${color}">${formatDistance(route.distance)}</span>
            `;
            routeSection.appendChild(routeHeader);
            
            // Add locations list
            const locationsList = document.createElement('ul');
            locationsList.className = 'location-list';
            
            route.locations.forEach((location, locationIndex) => {
                const li = document.createElement('li');
                li.className = 'location-item';
                li.setAttribute('data-lat', location.lat);
                li.setAttribute('data-lng', location.lng);
                
                li.innerHTML = `
                    <div class="location-header">
                        <span class="location-number" style="color: ${color}">${locationIndex + 1}</span>
                        <h3 class="location-title" style="color: ${color}">${location.name}</h3>
                    </div>
                    <p class="location-address">${formatAddress(location)}</p>
                `;
                
                // Add click event listener to the entire list item
                li.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const lat = parseFloat(li.dataset.lat);
                    const lng = parseFloat(li.dataset.lng);
                    
                    if (!isNaN(lat) && !isNaN(lng)) {
                        // First find and open the marker's popup
                        const marker = markerMap.get(location.id);
                        if (marker) {
                            marker.openPopup();
                        }
                        
                        // Then pan to location
                        map.flyTo([lat, lng], 18, {
                            duration: 1.5,
                            easeLinearity: 0.25
                        });
                    }
                });

                locationsList.appendChild(li);
            });
            
            routeSection.appendChild(locationsList);
            container.appendChild(routeSection);
        });
    }

    // Function to get loop letter from index (A, B, C, etc.)
    function getLoopLetter(index) {
        return String.fromCharCode(65 + index); // 65 is ASCII for 'A'
    }

    // Function to create marker icon
    function createMarkerIcon(loopLetter, locationNumber, color) {
        const markerHtml = `<div class="custom-marker">${loopLetter}${locationNumber}</div>`;
        return L.divIcon({
            html: markerHtml,
            className: 'custom-div-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
    }

    // Function to create Google Street View URL
    function createStreetViewUrl(location) {
        return location.googleMapsLink;
    }

    // Function to format address with building name, architect, and year
    function formatAddress(location) {
        if (!location.name) return location.address;
        
        const architect = location.architect ? `${location.architect}` : '';
        const year = location.year ? ` (${location.year})` : '';
        const details = architect || year ? `${architect}${year} — ` : '';
        return `${details}${location.address}`;
    }

    // Function to toggle description visibility
    function toggleDescription(index) {
        event.stopPropagation();
        const desc = document.getElementById(`description-${index}`);
        const arrow = document.getElementById(`arrow-${index}`);
        if (desc.style.display === 'none' || !desc.style.display) {
            desc.style.display = 'block';
            arrow.innerHTML = '▼';
        } else {
            desc.style.display = 'none';
            arrow.innerHTML = '▶';
        }
    }

    // Function to toggle the entire list
    function toggleLocationList() {
        const list = document.querySelector('.location-list');
        const panel = document.getElementById('info-panel');
        const toggleBtn = document.getElementById('toggle-list');
        
        if (list.style.display === 'none' || !list.style.display) {
            list.style.display = 'block';
            toggleBtn.innerHTML = '▼ Hide Locations';
            panel.classList.remove('collapsed');
        } else {
            list.style.display = 'none';
            toggleBtn.innerHTML = '▶ Show Locations';
            panel.classList.add('collapsed');
        }
    }

    // Palm Springs inspired colors for routes
    const routeColors = [
        '#FF6B6B',  // Palm Pink
        '#4CACBC',  // Pool Blue
        '#FFD93D',  // Sunset Yellow
        '#98D8AA',  // Cactus Green
        '#FFA07A'   // Desert Orange
    ];

    // Function to create marker
    function createMarker(location, loopLetter, number, color) {
        const markerHtml = `
            <div class="custom-marker" style="background-color: ${color}">
                ${loopLetter}${number}
            </div>`;
        
        const icon = L.divIcon({
            html: markerHtml,
            className: 'custom-div-icon',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        const marker = L.marker([location.lat, location.lng], { 
            icon,
            locationId: location.id  // Store the location ID with the marker
        });
        marker.bindPopup(createPopupContent(location));
        markers.addLayer(marker);
        
        return marker;
    }

    // Function to pan and zoom to a location
    function panToLocation(locationId) {
        const location = findLocationById(locationId);
        
        if (location) {
            // Pan to location with animation
            map.flyTo([location.lat, location.lng], 18, {
                duration: 1.5,
                easeLinearity: 0.25
            });
            
            // Open the marker's popup
            const marker = markerMap.get(locationId);
            if (marker) {
                marker.openPopup();
            }
        }
    }

    // Function to load and display locations
    async function loadLocations() {
        try {
            showLoading();
            const maxDistanceKm = toKilometers(userPreferences.maxDistance, userPreferences.distanceUnit);
            
            const response = await fetch(`/api/locations?maxDistance=${maxDistanceKm}`);
            const data = await response.json();
            window.currentRoutes = data.routes;
            window.currentTotalDistance = data.total_distance;

            // Clear existing markers and routes
            markers.clearLayers();
            markerMap.clear();
            
            // Remove existing polylines
            map.eachLayer((layer) => {
                if (layer instanceof L.Polyline && !(layer instanceof L.TileLayer)) {
                    map.removeLayer(layer);
                }
            });
            
            // Create a map to store route information by location ID
            const locationRouteMap = new Map();
            
            // First pass: create markers and store route information
            data.routes.forEach((route, routeIndex) => {
                const color = routeColors[routeIndex % routeColors.length];
                const loopLetter = getLoopLetter(routeIndex);
                
                // Add markers for this route and store route info
                route.locations.forEach((location, index) => {
                    const marker = createMarker(location, loopLetter, index + 1, color);
                    markerMap.set(location.id, marker);
                    // Store route information for this location
                    locationRouteMap.set(location.id, {
                        routeIndex: routeIndex,
                        color: color
                    });
                });
            });

            // Second pass: draw route segments
            if (data.route_segments) {
                data.route_segments.forEach(segment => {
                    if (typeof segment.route_index === 'number') {
                        const color = routeColors[segment.route_index % routeColors.length];
                        
                        if (segment.polyline) {
                            const coordinates = decodePolyline(segment.polyline);
                            if (coordinates && coordinates.length > 0) {
                                L.polyline(coordinates, {
                                    color: color,
                                    weight: 4,
                                    opacity: 0.7,
                                    lineJoin: 'round'
                                }).addTo(map);
                            }
                        } else {
                            // Draw straight line if no polyline is available
                            const coords = [
                                [segment.start.lat, segment.start.lng],
                                [segment.end.lat, segment.end.lng]
                            ];
                            L.polyline(coords, {
                                color: color,
                                weight: 4,
                                opacity: 0.7,
                                lineJoin: 'round',
                                dashArray: '5, 10'
                            }).addTo(map);
                        }
                    }
                });
            }

            // Add marker cluster group to map
            map.addLayer(markers);
            
            // Update info panel with all routes
            updateInfoPanel(data.routes);

        } catch (error) {
            console.error('Error loading locations:', error);
        } finally {
            hideLoading();
        }
    }

    // Function to create popup content
    function createPopupContent(location) {
        const popupContent = `
            <div class="popup-content">
                <h3>${location.name}</h3>
                <p>${formatAddress(location)}</p>
                <a href="${createStreetViewUrl(location)}" target="_blank" rel="noopener noreferrer">View in Google Maps</a>
            </div>
        `;
        return popupContent;
    }

    // Export functions for use in main.js
    window.loadLocations = loadLocations;
    window.updateInfoPanel = updateInfoPanel;
    window.panToLocation = panToLocation;
    window.findLocationById = findLocationById;

    // Loading state functions
    function showLoading() {
        document.getElementById('loading-overlay').style.display = 'flex';
    }

    function hideLoading() {
        document.getElementById('loading-overlay').style.display = 'none';
    }

    // Initialize with default settings
    loadLocations(5);  // Default 5km

    // Settings panel functionality
    document.getElementById('apply-settings').addEventListener('click', async () => {
        const maxDistance = parseFloat(document.getElementById('max-distance').value);
        const unit = document.getElementById('distance-unit').value;
        
        userPreferences.maxDistance = maxDistance;
        userPreferences.distanceUnit = unit;
        
        // Save to localStorage
        localStorage.setItem('maxDistance', maxDistance);
        localStorage.setItem('distanceUnit', unit);
        
        // Show loading while recalculating routes
        showLoading();
        document.querySelector('.loading-text').textContent = 'Recalculating routes...';
        
        // Reload locations with new max distance
        await loadLocations();
        
        // Reset loading text
        document.querySelector('.loading-text').textContent = 'Calculating routes...';
    });

    // Initialize settings form
    document.getElementById('max-distance').value = userPreferences.maxDistance;
    document.getElementById('distance-unit').value = userPreferences.distanceUnit;
    
    const collapseButton = document.getElementById('collapse-panel');
    const panel = document.getElementById('info-panel');
    
    collapseButton.addEventListener('click', function() {
        panel.classList.toggle('collapsed');
    });
    
    // Add collapse button event listener
    document.getElementById('collapse-panel').addEventListener('click', function() {
        document.getElementById('info-panel').classList.toggle('collapsed');
    });

    // Watch user's location
    function startLocationTracking() {
        if ("geolocation" in navigator) {
            navigator.geolocation.watchPosition(function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const accuracy = position.coords.accuracy;

                // Remove previous marker and circle
                if (userMarker) {
                    map.removeLayer(userMarker);
                }
                if (userAccuracyCircle) {
                    map.removeLayer(userAccuracyCircle);
                }

                // Add accuracy circle
                userAccuracyCircle = L.circle([lat, lng], {
                    radius: accuracy,
                    color: '#136AEC',
                    fillColor: '#136AEC',
                    fillOpacity: 0.15,
                    weight: 2
                }).addTo(map);

                // Add user marker
                userMarker = L.marker([lat, lng], {
                    icon: L.divIcon({
                        className: 'user-location-marker',
                        html: '<div class="user-dot"></div>',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    })
                }).addTo(map);

                console.log(`Updated user location: ${lat}, ${lng} (accuracy: ${accuracy}m)`);
            }, function(error) {
                console.error('Error getting location:', error);
            }, {
                enableHighAccuracy: true,
                maximumAge: 10000,
                timeout: 5000
            });
        } else {
            console.log("Geolocation is not supported by this browser.");
        }
    }

    startLocationTracking();

    // Add debug double-click handler to map
    map.on('dblclick', function(e) {
        console.log(`Latitude: ${e.latlng.lat}, Longitude: ${e.latlng.lng}`);
        // For easy copying to JSON:
        console.log(`"lat": ${e.latlng.lat},\n"lng": ${e.latlng.lng}`);
    });
});

function toggleDetails(locationId, event) {
    event.stopPropagation();
    const details = document.getElementById(`details-${locationId}`);
    const button = event.target;
    if (details.style.display === 'none' || !details.style.display) {
        details.style.display = 'block';
        button.innerHTML = `
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
    } else {
        details.style.display = 'none';
        button.innerHTML = `
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M15 15l-6 6 6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
    }
}

// Polyline decoder implementation
const decodePolyline = function(str, precision) {
    var index = 0,
        lat = 0,
        lng = 0,
        coordinates = [],
        shift = 0,
        result = 0,
        byte = null,
        latitude_change,
        longitude_change,
        factor = Math.pow(10, precision || 5);

    // Coordinates have variable length when encoded, so just keep
    // track of whether we've hit the end of the string. In each
    // loop iteration, a single coordinate is decoded.
    while (index < str.length) {
        // Reset shift, result, and byte
        byte = null;
        shift = 0;
        result = 0;

        do {
            byte = str.charCodeAt(index++) - 63;
            result |= (byte & 0x1f) << shift;
            shift += 5;
        } while (byte >= 0x20);

        latitude_change = ((result & 1) ? ~(result >> 1) : (result >> 1));

        shift = result = 0;

        do {
            byte = str.charCodeAt(index++) - 63;
            result |= (byte & 0x1f) << shift;
            shift += 5;
        } while (byte >= 0x20);

        longitude_change = ((result & 1) ? ~(result >> 1) : (result >> 1));

        lat += latitude_change;
        lng += longitude_change;

        coordinates.push([lat / factor, lng / factor]);
    }

    return coordinates;
};

// Function to draw a route between two points
function drawRouteLine(start, end, color = 'blue') {
    console.log('Drawing route line between:', start, end);
    L.polyline([start, end], {
        color: color,
        weight: 4,
        opacity: 0.7,
        lineJoin: 'round'
    }).addTo(map);
}
