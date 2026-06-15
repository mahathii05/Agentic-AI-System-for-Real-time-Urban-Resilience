const map = L.map('map').setView([10.0159, 76.3419], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: 'OpenStreetMap',
}).addTo(map);

let layers = [];
let clickMarker = null;

// -----------------------------------------------
// Page navigation
// -----------------------------------------------
function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

// -----------------------------------------------
// Fetch global city status (from monitor.py)
// -----------------------------------------------
async function fetchStatus() {
  try {
    const res = await fetch('/alert');
    const data = await res.json();
    document.getElementById('status').textContent = JSON.stringify(
      data,
      null,
      2
    );
    drawZones(data);
  } catch (err) {
    console.error('Failed to fetch alert:', err);
  }
}

// -----------------------------------------------
// Draw hazard zones on map
// -----------------------------------------------
function drawZones(data) {
  layers.forEach(l => map.removeLayer(l));
  layers = [];

  if (!data.zones) return;

  data.zones.forEach(zone => {
    let color = 'green';
    if (zone.type === 'flood') color = 'blue';
    if (zone.type === 'traffic') color = 'red';
    if (zone.type === 'crowd') color = 'orange';
    if (zone.type === 'power') color = 'yellow';

    const circle = L.circle([zone.lat, zone.lon], {
      radius: 1000,
      color: color,
      fillOpacity: 0.5,
    }).addTo(map);

    circle.bindPopup(`${zone.type.toUpperCase()} : ${zone.level}`);
    layers.push(circle);
  });
}

// -----------------------------------------------
// MAP CLICK → fetch location-based city status
// -----------------------------------------------
map.on('click', async function (e) {
  const lat = parseFloat(e.latlng.lat.toFixed(5));
  const lon = parseFloat(e.latlng.lng.toFixed(5));

  // Drop a pin on clicked location
  if (clickMarker) map.removeLayer(clickMarker);
  clickMarker = L.marker([lat, lon])
    .addTo(map)
    .bindPopup(`📍 Fetching status for<br>Lat: ${lat}, Lon: ${lon}`)
    .openPopup();

  // Switch to City Status tab and show loading state
  showPage('city-status');
  document.getElementById('status').textContent =
    `⏳ Fetching city status for:\nLat: ${lat}, Lon: ${lon}\n\nPlease wait...`;

  try {
    const res = await fetch('/location-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lon }),
    });

    const data = await res.json();

    // Merge clicked coordinates into the display
    const output = {
      clicked_location: { lat, lon },
      ...data,
    };

    document.getElementById('status').textContent = JSON.stringify(
      output,
      null,
      2
    );

    // Update map pin popup with risk level
    clickMarker
      .setPopupContent(
        `📍 Lat: ${lat}, Lon: ${lon}<br><b>${data.level || 'Status loaded'}</b>`
      )
      .openPopup();
  } catch (err) {
    document.getElementById('status').textContent =
      `❌ Error fetching status for Lat: ${lat}, Lon: ${lon}\n\n${err}`;
  }
});

// -----------------------------------------------
// CHAT — calls /claude endpoint
// -----------------------------------------------
async function sendMessage() {
  const input = document.getElementById('chatinput');
  const msg = input.value.trim();
  if (!msg) return;

  const box = document.getElementById('chatbox');
  box.innerHTML += `<div><b>You:</b> ${msg}</div>`;
  input.value = '';

  try {
    const res = await fetch('/claude', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg }),
    });

    const data = await res.json();
    box.innerHTML += `<div><b>AI:</b> ${data.reply || data.error}</div>`;
  } catch (err) {
    box.innerHTML += `<div><b>AI:</b> Error contacting server.</div>`;
  }

  box.scrollTop = box.scrollHeight;
}

setInterval(fetchStatus, 8000);
fetchStatus();
