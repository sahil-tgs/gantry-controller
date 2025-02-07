import asyncio
import websockets
import json
from controller import Robot, Motor

# Control and performance settings
CONTROL_STEP = 16  # Update interval in milliseconds - higher value = slower response but less CPU usage
RECONNECT_DELAY = 5  # Seconds to wait before attempting to reconnect
CONNECTION_TIMEOUT = 30  # Seconds to wait for initial connection

# Robot movement constraints
MAX_WHEEL_SPEED = 2.0    # Maximum speed for the gantry wheels
MAX_BRIDGE_SPEED = 0.5   # Maximum speed for bridge movement
MAX_LIFT_SPEED = 0.3     # Maximum speed for vertical lift
MAX_TURRET_SPEED = 0.5   # Maximum speed for turret rotation

# Gripper positions
GRIPPER_OPEN = 0.0       # Position value for open grippers
GRIPPER_CLOSE = 0.1      # Position value for closed grippers

# Control sensitivity
DEADZONE = 0.05          # Minimum input threshold to prevent drift

class GantryController:
    def __init__(self):
        """Initialize the gantry robot controller and set up all motor devices."""
        self.robot = Robot()
        
        # Initialize all movement motors with their device names
        self.motors = {
            'wheel1': self.robot.getDevice('wheel1_motor'),
            'wheel2': self.robot.getDevice('wheel2_motor'),
            'wheel3': self.robot.getDevice('wheel3_motor'),
            'wheel4': self.robot.getDevice('wheel4_motor'),
            'bridge': self.robot.getDevice('bridge_motor'),
            'lift': self.robot.getDevice('lift_motor'),
            'turret': self.robot.getDevice('turret_motor')
        }

        # Initialize gripper motors separately
        self.grippers = {
            'grip1': self.robot.getDevice('grip_motor1'),
            'grip2': self.robot.getDevice('grip_motor2')
        }

        self._initialize_motors()

    def _initialize_motors(self):
        """Set up initial motor positions and velocities."""
        # Initialize continuous rotation motors
        for motor_name in ['wheel1', 'wheel2', 'wheel3', 'wheel4', 'bridge', 'turret']:
            if self.motors[motor_name]:
                self.motors[motor_name].setPosition(float('inf'))  # Allow continuous rotation
                self.motors[motor_name].setVelocity(0.0)          # Start stationary

        # Special initialization for lift motor
        if self.motors['lift']:
            self.lift_position = 0.0
            self.motors['lift'].setPosition(0.0)
            print("Lift motor initialized")

    def handle_movement(self, axes):
        """Process movement commands from controller input."""
        try:
            # Calculate movement speeds with deadzone filtering
            gantry_speed = 0.0 if abs(axes.get('left_x', 0)) < DEADZONE else axes.get('left_x', 0) * MAX_WHEEL_SPEED
            bridge_speed = 0.0 if abs(axes.get('right_x', 0)) < DEADZONE else axes.get('right_x', 0) * MAX_BRIDGE_SPEED
            turret_speed = 0.0 if abs(axes.get('left_y', 0)) < DEADZONE else -axes.get('left_y', 0) * MAX_TURRET_SPEED

            # Handle lift movement with position control
            lift_input = axes.get('right_y', 0)
            if abs(lift_input) > DEADZONE:
                # Update lift position with small increments for smooth motion
                self.lift_position -= lift_input * 0.005
                self.lift_position = max(0.0, min(1.0, self.lift_position))
                if self.motors['lift']:
                    self.motors['lift'].setPosition(self.lift_position)

            # Apply wheel speeds uniformly to all wheels
            for wheel in ['wheel1', 'wheel2', 'wheel3', 'wheel4']:
                if self.motors[wheel]:
                    self.motors[wheel].setVelocity(gantry_speed)

            # Set bridge and turret speeds
            if self.motors['bridge']: self.motors['bridge'].setVelocity(bridge_speed)
            if self.motors['turret']: self.motors['turret'].setVelocity(turret_speed)

        except Exception as e:
            print(f"Movement error: {e}")
            self.stop_all_motors()

    def handle_grippers(self, buttons):
        """Control gripper open/close operations."""
        try:
            if buttons.get('a', False):      # 'A' button opens grippers
                for gripper in self.grippers.values():
                    if gripper:
                        gripper.setPosition(GRIPPER_OPEN)
            elif buttons.get('b', False):    # 'B' button closes grippers
                for gripper in self.grippers.values():
                    if gripper:
                        gripper.setPosition(GRIPPER_CLOSE)
        except Exception as e:
            print(f"Gripper error: {e}")

    def stop_all_motors(self):
        """Emergency stop function for all motors."""
        # Stop all movement motors
        for motor_name in ['wheel1', 'wheel2', 'wheel3', 'wheel4', 'bridge', 'turret']:
            if self.motors[motor_name]:
                self.motors[motor_name].setVelocity(0.0)
        
        # Maintain current lift position for safety
        if self.motors['lift']:
            self.motors['lift'].setPosition(self.lift_position)

    async def run(self):
        """Main control loop with WebSocket communication."""
        # uri = "ws://localhost:3000"
        uri = "wss://gantry-controller.up.railway.app"
        print(f"Starting controller... Attempting to connect to {uri}")
        
        while True:
            try:
                # Attempt WebSocket connection with timeout
                async with websockets.connect(
                    uri,
                    ping_interval=None,  # Disable automatic ping to handle connection manually
                    close_timeout=CONNECTION_TIMEOUT
                ) as websocket:
                    print("Successfully connected to gamepad server")
                    
                    while self.robot.step(CONTROL_STEP) != -1:
                        try:
                            # Receive and process controller state
                            msg = await websocket.recv()
                            state = json.loads(msg)
                            
                            # Debug output for monitoring
                            print(f"Received state update")
                            
                            # Update robot state based on controller input
                            self.handle_movement(state.get('axes', {}))
                            self.handle_grippers(state.get('buttons', {}))
                            
                        except websockets.exceptions.ConnectionClosed:
                            print("WebSocket connection lost, attempting to reconnect...")
                            break
                        except json.JSONDecodeError as e:
                            print(f"Invalid controller data received: {e}")
                            continue
                        except Exception as e:
                            print(f"Operation error: {e}")
                            self.stop_all_motors()
                            
            except websockets.exceptions.InvalidStatusCode as e:
                print(f"Server connection error: {e}")
                print("This usually means the server isn't accepting WebSocket connections.")
                await asyncio.sleep(RECONNECT_DELAY)
            except websockets.exceptions.InvalidURI as e:
                print(f"Invalid WebSocket URL: {e}")
                print("Please check the connection URI format.")
                break  # Exit if the URI is fundamentally invalid
            except Exception as e:
                print(f"Connection error: {e}")
                print(f"Retrying in {RECONNECT_DELAY} seconds...")
                self.stop_all_motors()
                await asyncio.sleep(RECONNECT_DELAY)

def main():
    """Entry point for the gantry controller application."""
    controller = GantryController()
    try:
        asyncio.get_event_loop().run_until_complete(controller.run())
    except KeyboardInterrupt:
        print("\nController stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("Shutting down controller")

if __name__ == "__main__":
    main()