document.addEventListener('DOMContentLoaded', function() {
    let map = L.map('map').setView([33.8303, -116.5453], 13);
    let markers = L.markerClusterGroup();
    let locationList = document.createElement('div');
    locationList.className = 'location-list';
    
    // User preferences (with defaults)
    let userPreferences = {
        units: localStorage.getItem('distanceUnit') || 'miles',
        defaultRouteDistance: 3 // in miles
    };

    // Define route colors
    const routeColors = [
        '#FF6B6B',  // Palm Pink
        '#4CACBC',  // Pool Blue
        '#98D8AA',  // Cactus Green
        '#FFD93D',  // Sunset Yellow
        '#FFA07A'   // Desert Orange
    ];
    
    // Add the tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: ' OpenStreetMap contributors'
    }).addTo(map);
    
    // Add location control
    L.control.locate().addTo(map);
    
    // Function to calculate distance between two points (in meters)
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371e3; // Earth's radius in meters
        const φ1 = lat1 * Math.PI/180;
        const φ2 = lat2 * Math.PI/180;
        const Δφ = (lat2-lat1) * Math.PI/180;
        const Δλ = (lon2-lon1) * Math.PI/180;

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                Math.cos(φ1) * Math.cos(φ2) *
                Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

        return R * c;
    }
    
    // Function to format distance based on user preferences
    function formatDistance(kilometers) {
        const miles = kilometers * 0.621371;
        if (userPreferences.units === 'miles') {
            return `${miles.toFixed(1)} ${miles === 1 ? 'mile' : 'miles'}`;
        } else {
            return `${kilometers.toFixed(1)} ${kilometers === 1 ? 'kilometer' : 'kilometers'}`;
        }
    }
    
    // Function to get default distance in meters
    function getDefaultDistanceInMeters() {
        return userPreferences.defaultRouteDistance * 1609.34; // Convert miles to meters
    }
    
    // Fetch locations from the API
    fetch('/api/locations')
        .then(response => response.json())
        .then(data => {
            data.routes.forEach((route, routeIndex) => {
                const routeColor = routeColors[routeIndex % routeColors.length];
                
                // Create route section
                let routeSection = document.createElement('div');
                routeSection.className = 'route-section';
                
                // Create route header with distance
                let routeHeader = document.createElement('div');
                routeHeader.className = 'route-header';
                let distance = route.distance || userPreferences.defaultRouteDistance * 1.60934; // Convert default miles to km
                routeHeader.innerHTML = `
                    <h2 style="color: ${routeColor}">
                        Route ${String.fromCharCode(65 + routeIndex)}
                        <span class="route-distance" style="color: ${routeColor}">${formatDistance(distance)}</span>
                    </h2>
                `;
                routeSection.appendChild(routeHeader);
                
                // Create locations list for this route
                let routeLocations = document.createElement('div');
                routeLocations.className = 'route-locations';
                
                route.locations.forEach((location, locationIndex) => {
                    // Create marker with route color
                    let marker = L.marker([location.lat, location.lng], {
                        icon: L.divIcon({
                            className: 'custom-marker',
                            html: `<div style="background-color: ${routeColor}; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold;">${locationIndex + 1}</div>`
                        })
                    });
                    markers.addLayer(marker);
                    
                    // Create list item
                    let li = document.createElement('div');
                    li.className = 'location-item';
                    
                    // Create title with number and name
                    let title = document.createElement('div');
                    title.className = 'location-title';
                    title.innerHTML = `
                        <span class="location-number">${locationIndex + 1}</span>
                        <span class="location-name">${location.name}</span>
                    `;
                    
                    // Create subtitle (architect and year)
                    let subtitle = document.createElement('div');
                    subtitle.className = 'location-subtitle';
                    subtitle.textContent = `${location.architect} (${location.year})`;
                    
                    // Create description
                    let description = document.createElement('div');
                    description.className = 'location-description';
                    description.textContent = location.description;
                    
                    // Add elements to list item
                    li.appendChild(title);
                    li.appendChild(subtitle);
                    li.appendChild(description);
                    
                    // Add click handler
                    li.addEventListener('click', () => {
                        map.setView([location.lat, location.lng], 16);
                        marker.openPopup();
                    });
                    
                    routeLocations.appendChild(li);
                    
                    // Create popup
                    let popup = L.popup()
                        .setLatLng([location.lat, location.lng])
                        .setContent(`
                            <div class="popup-content">
                                <h3>${location.name}</h3>
                                <p>${location.architect} (${location.year})</p>
                                <p>${location.description}</p>
                            </div>
                        `);
                    
                    marker.bindPopup(popup);
                });
                
                routeSection.appendChild(routeLocations);
                locationList.appendChild(routeSection);
            });
            
            // Add markers to map
            map.addLayer(markers);
            
            // Add location list to info panel
            document.querySelector('#info-panel').appendChild(locationList);
        })
        .catch(error => {
            console.error('Error fetching locations:', error);
        });
    
    // Panel collapse/expand functionality
    const infoPanel = document.querySelector('#info-panel');
    const collapseButton = document.querySelector('#collapse-panel');
    
    collapseButton.addEventListener('click', () => {
        infoPanel.classList.toggle('collapsed');
    });
});
