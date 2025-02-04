// Main application logic
document.addEventListener('DOMContentLoaded', function() {
    // Settings panel functionality
    const settingsPanel = document.getElementById('settings-panel');
    const settingsButton = document.getElementById('settings-button');
    const applySettingsButton = document.getElementById('apply-settings');
    const maxDistanceInput = document.getElementById('max-distance');
    const distanceUnitSelect = document.getElementById('distance-unit');
    
    // Initialize settings from localStorage
    const savedUnit = localStorage.getItem('distanceUnit') || 'km';
    const savedMaxDistance = localStorage.getItem('maxDistance') || '5';
    
    distanceUnitSelect.value = savedUnit;
    maxDistanceInput.value = savedMaxDistance;

    // Add input validation
    maxDistanceInput.addEventListener('input', function(e) {
        const value = e.target.value;
        // Remove any non-numeric characters except decimal point
        let sanitized = value.replace(/[^\d.]/g, '');
        // Ensure only one decimal point
        const parts = sanitized.split('.');
        if (parts.length > 2) {
            sanitized = parts[0] + '.' + parts.slice(1).join('');
        }
        // Update value if it changed
        if (value !== sanitized) {
            e.target.value = sanitized;
        }
    });
    
    // Settings button click handler
    settingsButton.addEventListener('click', () => {
        settingsPanel.classList.toggle('hidden');
    });
    
    // Apply settings click handler
    applySettingsButton.addEventListener('click', () => {
        let maxDistance = parseFloat(maxDistanceInput.value);
        const unit = distanceUnitSelect.value;
        
        // Validate the distance
        if (isNaN(maxDistance) || maxDistance <= 0) {
            alert('Please enter a valid positive number for the maximum distance.');
            return;
        }

        // Set reasonable limits based on units
        const maxLimit = unit === 'km' ? 20 : 12; // 20km or 12mi
        if (maxDistance > maxLimit) {
            alert(`Maximum distance cannot exceed ${maxLimit} ${unit}.`);
            maxDistance = maxLimit;
            maxDistanceInput.value = maxLimit;
        }
        
        localStorage.setItem('distanceUnit', unit);
        localStorage.setItem('maxDistance', maxDistance);
        
        // Convert to kilometers if needed
        const maxDistanceKm = unit === 'mi' ? maxDistance * 1.60934 : maxDistance;
        
        // Show loading state
        if (typeof showLoading === 'function') {
            showLoading();
        }
        
        // Reload locations with new settings
        if (typeof loadLocations === 'function') {
            loadLocations(maxDistanceKm).then(() => {
                if (typeof hideLoading === 'function') {
                    hideLoading();
                }
            });
        }
        
        settingsPanel.classList.add('hidden');
    });
    
    // Initialize with saved settings
    const initialMaxDistance = savedUnit === 'mi' ? 
        parseFloat(savedMaxDistance) * 1.60934 : 
        parseFloat(savedMaxDistance);
    
    if (typeof loadLocations === 'function') {
        loadLocations(initialMaxDistance);
    }
});
