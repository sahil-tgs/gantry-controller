// server/server.js
const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, '../public')));

// Store connected clients
const clients = new Set();

// WebSocket connection handling
wss.on('connection', (ws) => {
    console.log('New client connected');
    clients.add(ws);

    // Send initial state
    ws.send(JSON.stringify({
        axes: { left_x: 0, left_y: 0, right_x: 0, right_y: 0 },
        buttons: { a: false, b: false }
    }));

    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            
            // Broadcast to all other clients
            clients.forEach(client => {
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    client.send(JSON.stringify(data));
                }
            });
        } catch (error) {
            console.error('Error processing message:', error);
        }
    });

    ws.on('close', () => {
        console.log('Client disconnected');
        clients.delete(ws);
    });

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        clients.delete(ws);
    });
});

// Get local network interfaces
function getLocalAddresses() {
    const { networkInterfaces } = require('os');
    const nets = networkInterfaces();
    const results = [];

    for (const name of Object.keys(nets)) {
        for (const net of nets[name]) {
            // Skip over non-IPv4 and internal addresses
            if (net.family === 'IPv4' && !net.internal) {
                results.push(net.address);
            }
        }
    }
    return results;
}

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log('\n=== Gantry Control Server ===\n');
    console.log(`Local access: http://localhost:${PORT}`);
    console.log('\nAccess from mobile devices using:');
    getLocalAddresses().forEach(ip => {
        console.log(`http://${ip}:${PORT}`);
    });
    console.log('\nServer is running...');
});