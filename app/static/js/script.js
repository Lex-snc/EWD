// Function to save and send SMS message
function saveMessage() {
    const messageText = document.getElementById('editable-message').value.trim();
    
    if (!messageText) {
        Swal.fire({
            icon: 'warning',
            title: 'Empty Message',
            text: 'Please enter a message before sending.'
        });
        return;
    }

    // Show loading state
    Swal.fire({
        title: 'Sending message...',
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // Send message to backend
    fetch('/send_sms', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: messageText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Success!',
                text: 'Message sent successfully'
            });
            // Clear the message box after successful send
            document.getElementById('editable-message').value = '';
        } else {
            throw new Error(data.message || 'Failed to send message');
        }
    })
    .catch(error => {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Failed to send message. Please try again.'
        });
    });
}

// Character count functionality
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('editable-message');
    const charCount = document.getElementById('char-count');

    messageInput.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = count;
        
        // Visual feedback when approaching limit
        if (count > 140) {
            charCount.style.color = '#e74c3c';
        } else if (count > 120) {
            charCount.style.color = '#f39c12';
        } else {
            charCount.style.color = '#666';
        }
    });
});

// Function to update monitoring data
function updateMonitoringData() {
    fetch('/monitor')
        .then(response => response.json())
        .then(data => {
            document.getElementById('monitor-terminal').innerHTML = `
                <p>Water Level: ${data.water_level} cm</p>
                <p>Current: ${data.current} A</p>
                <p>Timestamp: ${data.timestamp}</p>
            `;
        })
        .catch(error => console.error('Error updating monitoring data:', error));
}

// Update monitoring data every 5 seconds
setInterval(updateMonitoringData, 5000);

let charts = {};

function getWeatherIcon(code) {
    if (code <= 1) return 'fa-sun';
    if (code <= 3) return 'fa-cloud-sun';
    if (code <= 48) return 'fa-cloud';
    if (code <= 57) return 'fa-cloud-rain';
    if (code <= 67) return 'fa-cloud-showers-heavy';
    if (code <= 77) return 'fa-snowflake';
    if (code <= 82) return 'fa-cloud-rain';
    if (code <= 86) return 'fa-snowflake';
    return 'fa-bolt';
}

function createChart(ctx, label, data, labels, color) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                tension: 0.4,
                fill: false,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 9
                        }
                    },
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 9
                        },
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 5
                    },
                    grid: {
                        display: false
                    }
                }
            },
            layout: {
                padding: {
                    left: 5,
                    right: 5,
                    top: 5,
                    bottom: 5
                }
            }
        }
    });
}

function updateCharts(hourlyData) {
    const nextHours = hourlyData.time.slice(0, 24);
    const temps = hourlyData.temperature.slice(0, 24);
    const humidity = hourlyData.humidity.slice(0, 24);
    const precip = hourlyData.precipitation_prob.slice(0, 24);
    const wind = hourlyData.wind_speed.slice(0, 24);

    if (charts.temp) charts.temp.destroy();
    if (charts.humidity) charts.humidity.destroy();
    if (charts.precip) charts.precip.destroy();
    if (charts.wind) charts.wind.destroy();

    charts.temp = createChart(document.getElementById('tempChart'), 'Temperature', temps, nextHours, '#ff6384');
    charts.humidity = createChart(document.getElementById('humidityChart'), 'Humidity', humidity, nextHours, '#36a2eb');
    charts.precip = createChart(document.getElementById('precipChart'), 'Precipitation', precip, nextHours, '#4bc0c0');
    charts.wind = createChart(document.getElementById('windChart'), 'Wind Speed', wind, nextHours, '#ff9f40');

    // Update current values
    document.getElementById('current-temp').textContent = temps[0].toFixed(1) + '°C';
    document.getElementById('current-humidity').textContent = humidity[0].toFixed(1) + '%';
    document.getElementById('current-precip').textContent = precip[0].toFixed(1) + '%';
    document.getElementById('current-wind').textContent = wind[0].toFixed(1) + ' km/h';
}

function updateForecast(dailyData) {
    const container = document.getElementById('forecast-container');
    container.innerHTML = '';

    for (let i = 0; i < 3; i++) {
        const date = new Date(dailyData.time[i]);
        const card = document.createElement('div');
        card.className = 'weather-card';
        card.innerHTML = `
            <h4>${date.toLocaleDateString()}</h4>
            <i class="fas ${getWeatherIcon(dailyData.weather_code[i])} weather-icon"></i>
            <p>High: ${dailyData.temp_max[i].toFixed(1)}°C</p>
            <p>Low: ${dailyData.temp_min[i].toFixed(1)}°C</p>
            <p>Precipitation: ${dailyData.precipitation[i].toFixed(1)}mm</p>
        `;
        container.appendChild(card);
    }
}

// User location coordinates
let userLatitude = 52.52;  // Default latitude
let userLongitude = 13.41; // Default longitude
let isLocationDetectionInProgress = false;

// Function to get user's current location
function getUserLocation() {
    // Show loading state
    document.getElementById('location-display').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting your location...';
    isLocationDetectionInProgress = true;
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            (position) => {
                userLatitude = position.coords.latitude;
                userLongitude = position.coords.longitude;
                console.log(`Location obtained: ${userLatitude}, ${userLongitude}`);
                
                // Show coordinates while we fetch the location name
                document.getElementById('location-display').innerHTML = `<i class="fas fa-map-marker-alt"></i> ${userLatitude.toFixed(4)}, ${userLongitude.toFixed(4)}`;
                
                // Refresh weather data with new coordinates
                refreshWeatherData();
                isLocationDetectionInProgress = false;
            },
            // Error callback
            (error) => {
                console.error('Error getting location:', error);
                
                let errorMessage = '';
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location access denied. Using default location.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information unavailable. Using default location.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out. Using default location.';
                        break;
                    default:
                        errorMessage = 'Unknown error occurred. Using default location.';
                }
                
                document.getElementById('location-display').innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${errorMessage}`;
                
                // Use default coordinates
                refreshWeatherData();
                isLocationDetectionInProgress = false;
            },
            // Options
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        console.error('Geolocation is not supported by this browser');
        document.getElementById('location-display').innerHTML = '<i class="fas fa-times-circle"></i> Geolocation not supported';
        
        // Use default coordinates
        refreshWeatherData();
        isLocationDetectionInProgress = false;
    }
}

async function refreshWeatherData() {
    try {
        if (!isLocationDetectionInProgress) {
            document.getElementById('location-display').innerHTML = '<i class="fas fa-sync fa-spin"></i> Updating weather data...';
        }
        
        const response = await fetch(`/get_weather_data?lat=${userLatitude}&lon=${userLongitude}&time=${new Date().getTime()}`);
        const data = await response.json();
        
        if (data.success) {
            updateCharts(data.hourly_data);
            updateForecast(data.daily_data);
            
            // Update location name if available
            if (data.location_name && !isLocationDetectionInProgress) {
                const timestamp = new Date().toLocaleTimeString();
                document.getElementById('location-display').innerHTML = 
                    `<i class="fas fa-map-marker-alt"></i> ${data.location_name} <span class="update-time">(Updated: ${timestamp})</span>`;
            }
        } else {
            console.error('Failed to fetch weather data:', data.error);
            if (!isLocationDetectionInProgress) {
                document.getElementById('location-display').innerHTML = 
                    `<i class="fas fa-exclamation-circle"></i> Error updating weather data`;
            }
        }
    } catch (error) {
        console.error('Error fetching weather data:', error);
        if (!isLocationDetectionInProgress) {
            document.getElementById('location-display').innerHTML = 
                `<i class="fas fa-exclamation-circle"></i> Error updating weather data`;
        }
    }
}

// Initial location and data load
getUserLocation();

// Auto-refresh location and weather data every 15 minutes
setInterval(getUserLocation, 900000);

// Auto-refresh weather data every 5 minutes (without location refresh)
setInterval(() => refreshWeatherData(), 300000);

// Character count for SMS
document.getElementById('editable-message').addEventListener('input', function() {
    document.getElementById('char-count').textContent = this.value.length;
});

// Real-time clock function
function updateClock() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    
    // Format options for date display
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    
    document.getElementById('digital-clock').textContent = `${hours}:${minutes}:${seconds}`;
    document.getElementById('date-display').textContent = now.toLocaleDateString('en-US', options);
}

// Initial clock update
updateClock();

// Update clock every second
setInterval(updateClock, 1000);
