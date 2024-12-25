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
    
    // Settings button click handler
    settingsButton.addEventListener('click', () => {
        settingsPanel.classList.toggle('hidden');
    });
    
    // Apply settings click handler
    applySettingsButton.addEventListener('click', () => {
        const maxDistance = maxDistanceInput.value;
        const unit = distanceUnitSelect.value;
        
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
