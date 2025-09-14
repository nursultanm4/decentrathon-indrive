// View management
function initializeViewManagement() {
    const buttons = document.querySelectorAll('.nav-button');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            // Update button states
            buttons.forEach(b => b.classList.remove('active'));
            button.classList.add('active');
            
            // Show corresponding view
            const viewName = button.dataset.view;
            document.querySelectorAll('.dashboard-view').forEach(view => {
                view.classList.add('hidden');
            });
            document.getElementById(`${viewName}-view`).classList.remove('hidden');
            
            // Load data for the view
            if (viewName === 'safety') {
                fetchSafetyMetrics();
                fetchTripDetails();
            } else if (viewName === 'routes') {
                // We'll implement this later
                console.log('Routes view selected - to be implemented');
            }
        });
    });
}


async function fetchSafetyMetrics() {
    try {
        const response = await fetch('/api/safety-metrics');
        const data = await response.json();
        document.getElementById('total-trips').textContent = data.total_trips;
        document.getElementById('avg-speed').textContent = data.avg_speed.toFixed(2);
        document.getElementById('high-speed-points').textContent = data.high_speed_points.toFixed(2);
        document.getElementById('unusual-routes').textContent = data.unusual_routes;
        document.getElementById('sharp-declines').textContent = data.sharp_declines;

        // Safety events horizontal bar chart
        const ctxEvents = document.getElementById('safety-events-chart').getContext('2d');
        if (window.safetyEventsChart) window.safetyEventsChart.destroy();
        window.safetyEventsChart = new Chart(ctxEvents, {
            type: 'bar',
            data: {
                labels: ['Unusual Routes', 'Sharp Declines', 'Sharp Turns'],
                datasets: [{
                    label: 'Count',
                    data: [data.unusual_routes, data.sharp_declines, data.sharp_turns],
                    backgroundColor: ['#4299e1', '#f6ad55', '#48bb78']
                }]
            },
            options: {
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });

        // Speed distribution chart
        const ctx = document.getElementById('speed-chart').getContext('2d');
        if (window.speedChart) window.speedChart.destroy();
        window.speedChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.speed_distribution.bins.slice(1).map((b, i) => `${data.speed_distribution.bins[i]}-${b} km/h`),
                datasets: [{
                    label: 'Speed Count',
                    data: data.speed_distribution.counts,
                    backgroundColor: '#2c5282'
                }]
            }
        });
    } catch (error) {
        console.error('Error fetching safety metrics:', error);
    }
}


let currentPage = 1;
const perPage = 10;

async function fetchTripDetails(page = 1) {
    try {
        const response = await fetch(`/api/trip-details?page=${page}&per_page=${perPage}`);
        const data = await response.json();
        const trips = data.trips;
        const total = data.total;

        const tbody = document.querySelector('#trip-metrics tbody');
        tbody.innerHTML = '';
        trips.forEach(trip => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${trip.trip_id}</td>
                <td>${trip.avg_speed}</td>
                <td>${trip.max_speed}</td>
                <td>${trip.avg_azimuth_change}</td>
                <td>${trip.sharp_turns}</td>
                <td>${trip.distance}</td>
            `;
            tbody.appendChild(row);
        });

        renderPagination(total, page);
    } catch (error) {
        console.error('Error fetching trip details:', error);
    }
}

function renderPagination(total, page) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    const totalPages = Math.ceil(total / perPage);

    // Show first 9 pages, then "..." and last page if needed
    let maxVisible = 9;
    for (let i = 1; i <= Math.min(totalPages, maxVisible); i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        if (i === page) btn.classList.add('active');
        btn.addEventListener('click', () => {
            currentPage = i;
            fetchTripDetails(currentPage);
        });
        pagination.appendChild(btn);
    }

    if (totalPages > maxVisible) {
        // Add "..."
        const dots = document.createElement('span');
        dots.textContent = '...';
        dots.style.padding = '0 8px';
        pagination.appendChild(dots);

        // Add last page button
        const lastBtn = document.createElement('button');
        lastBtn.textContent = totalPages;
        if (totalPages === page) lastBtn.classList.add('active');
        lastBtn.addEventListener('click', () => {
            currentPage = totalPages;
            fetchTripDetails(currentPage);
        });
        pagination.appendChild(lastBtn);
    }
}


// Update view management to reset page on tab switch
function initializeViewManagement() {
    const buttons = document.querySelectorAll('.nav-button');
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            button.classList.add('active');
            const viewName = button.dataset.view;
            document.querySelectorAll('.dashboard-view').forEach(view => {
                view.classList.add('hidden');
            });
            document.getElementById(`${viewName}-view`).classList.remove('hidden');
            if (viewName === 'safety') {
                fetchSafetyMetrics();
                currentPage = 1;
                fetchTripDetails(currentPage);
            } else if (viewName === 'routes') {
                fetchPopularRoutes();
            }
        });
    });
}


async function fetchPopularRoutes() {
    try {
        const response = await fetch('/api/popular-routes');
        const data = await response.json();
        document.getElementById('popular-areas').textContent =
            data.popular_starts.map(([loc, count]) => `${loc} (${count})`).join(', ');
        document.getElementById('busy-hours').textContent =
            data.popular_ends.map(([loc, count]) => `${loc} (${count})`).join(', ');
        document.getElementById('total-distance').textContent = data.total_routes;
        document.getElementById('popular-pairs').textContent =
            data.popular_pairs.map(([[start, end], count]) => `${start} → ${end} (${count})`).join(', ');

        // Chart: popular start locations
        const ctx = document.getElementById('routes-chart').getContext('2d');
        if (window.routesChart) window.routesChart.destroy();
        window.routesChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.popular_starts.map(([loc, _]) => loc),
                datasets: [{
                    label: 'Popular Start Locations',
                    data: data.popular_starts.map(([_, count]) => count),
                    backgroundColor: '#2c5282'
                }]
            }
        });

        // Chart: trip length distribution
        const ctx2 = document.getElementById('length-chart').getContext('2d');
        if (window.lengthChart) window.lengthChart.destroy();
        window.lengthChart = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: data.length_histogram.bins.slice(1).map((b, i) => `${data.length_histogram.bins[i]}-${b} km`),
                datasets: [{
                    label: 'Trip Count',
                    data: data.length_histogram.counts,
                    backgroundColor: '#68d391'
                }]
            }
        });
    } catch (error) {
        console.error('Error fetching popular routes:', error);
    }
}


// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeViewManagement();
    // Load initial view (safety)
    fetchSafetyMetrics();
    fetchTripDetails();
});