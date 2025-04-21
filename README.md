# Gantry Robot Web Controller

A versatile web-based control system for a gantry robot simulation. This project features a modern web interface for robot control, a Node.js WebSocket server for real-time communication, and a Python controller that integrates with the Webots robotics simulation environment.

## 🎯 Objective

The main objective of this project is to create a control system that:
- Provides intuitive remote control of a gantry robot simulation
- Enables real-time communication between the user interface and robot
- Offers precise control over multiple robot components
- Works seamlessly across different devices and platforms


## 🎥 Demo


https://github.com/user-attachments/assets/94be487f-4f85-4986-9a65-8ba2ac6bcf3e




## ✨ Features

### Multi-Axis Control
- Gantry movement (left/right)
- Bridge movement (forward/backward)
- Lift control (up/down)
- Turret rotation
- Gripper operation (open/close)

### Real-Time Communication
- WebSocket-based instant response
- Continuous state updates
- Automatic reconnection handling

### Safety Features
- Emergency stop functionality
- Movement deadzone for stability
- Speed limitations for controlled operation
- Position clamping for lift mechanism

### User Interface
- Touch-friendly mobile design
- Visual feedback for button states
- Connection status indicator
- Intuitive control layout

### Robust Error Handling
- Network disconnection recovery
- Motor fault protection
- Invalid command filtering
- Comprehensive error reporting

## 🛠️ Tech Stack

### Frontend
- HTML5
- CSS3 (with responsive design)
- Vanilla JavaScript (ES6+)
- WebSocket API

### Backend
- Node.js
- Express.js
- ws (WebSocket library)
- Compression middleware

### Robot Controller
- Python
- websockets library
- Webots Controller API
- asyncio for asynchronous operations

## 🚀 Getting Started

### Prerequisites
- Python 
- Node.js and npm
- Webots robotics simulator
- A modern web browser

### Server Setup

Clone the repository:
git clone https://github.com/your-username/gantry-controller.git
cd gantry-controller

Install server dependencies:
cd server
npm install

Start the WebSocket server:
npm start

### Controller Setup

Ensure you're in the project root:
cd gantry-controller

Install Python dependencies:
pip install websockets

Note: The controller will be loaded by Webots automatically when you run the simulation

### Accessing the Interface
- Local development: Open http://localhost:3000 in your browser
- Deployed version: Visit the Railway-hosted URL (when deployed)

## 📝 Usage

1. Start the Webots simulation with the gantry robot
2. Launch the WebSocket server
3. Open the web interface in your browser
4. Use the control buttons to operate the robot:
   - Left/Right arrows for gantry movement
   - Forward/Back for bridge control
   - Up/Down for lift operation
   - Rotation controls for turret
   - Open/Close buttons for gripper control

## 🔧 Configuration

The system can be configured through various parameters:
- CONTROL_STEP: Response time for robot updates (ms)
- MAX_SPEED values for different components
- DEADZONE: Minimum input threshold
- WebSocket connection settings

## 🤝 Contributing

Contributions are welcome! Please feel free to:
1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Submit a pull request

## 🔒 Security Considerations

- The WebSocket server implements basic security measures
- Client input validation prevents invalid commands
- Error handling protects against malformed data
- The system is designed for controlled network environments

## 🚧 Future Improvements

- Add authentication for remote access
- Implement custom control profiles
- Add motion recording and playback
- Create a virtual robot position display
- Add support for multiple simultaneous connections
- Implement emergency stop broadcasting

## 📄 Notes

This project was developed as part of a robotics control system demonstration, showcasing the integration of web technologies with robotic simulation. The system demonstrates real-time control capabilities, robust error handling, and responsive user interface design.

The project emphasizes practical aspects of robotics control, including:
- Real-time communication architecture
- Safety-first design principles
- Cross-platform compatibility
- User-friendly interface design
