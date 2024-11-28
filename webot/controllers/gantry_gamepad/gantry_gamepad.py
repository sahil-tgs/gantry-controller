import asyncio
import websockets
import json
from controller import Robot, Motor

# Optimize control loop
CONTROL_STEP = 16  # Reduced from 64 to 16ms for faster updates

# Speed limits
MAX_WHEEL_SPEED = 2.0
MAX_BRIDGE_SPEED = 0.5
MAX_LIFT_SPEED = 0.3
MAX_TURRET_SPEED = 0.5

# Gripper constants - Original values
GRIPPER_OPEN = 0.0
GRIPPER_CLOSE = 0.1

# Small deadzone for stability
DEADZONE = 0.05

class GantryController:
    def __init__(self):
        self.robot = Robot()
        
        # Initialize all motors at once
        self.motors = {
            'wheel1': self.robot.getDevice('wheel1_motor'),
            'wheel2': self.robot.getDevice('wheel2_motor'),
            'wheel3': self.robot.getDevice('wheel3_motor'),
            'wheel4': self.robot.getDevice('wheel4_motor'),
            'bridge': self.robot.getDevice('bridge_motor'),
            'lift': self.robot.getDevice('lift_motor'),
            'turret': self.robot.getDevice('turret_motor')
        }

        # Separate gripper initialization
        self.grippers = {
            'grip1': self.robot.getDevice('grip_motor1'),
            'grip2': self.robot.getDevice('grip_motor2')
        }

        # Initialize movement motors
        for motor_name in ['wheel1', 'wheel2', 'wheel3', 'wheel4', 'bridge', 'turret']:
            if self.motors[motor_name]:
                self.motors[motor_name].setPosition(float('inf'))
                self.motors[motor_name].setVelocity(0.0)

        # Special initialization for lift motor
        if self.motors['lift']:
            self.lift_position = 0.0
            self.motors['lift'].setPosition(0.0)  # Set initial position
            print("Lift motor initialized")

    def handle_movement(self, axes):
        try:
            # Process all movements in one pass
            gantry_speed = 0.0 if abs(axes.get('left_x', 0)) < DEADZONE else axes.get('left_x', 0) * MAX_WHEEL_SPEED
            bridge_speed = 0.0 if abs(axes.get('right_x', 0)) < DEADZONE else axes.get('right_x', 0) * MAX_BRIDGE_SPEED
            turret_speed = 0.0 if abs(axes.get('left_y', 0)) < DEADZONE else -axes.get('left_y', 0) * MAX_TURRET_SPEED

            # Handle lift movement with position control
            lift_input = axes.get('right_y', 0)
            if abs(lift_input) > DEADZONE:
                # Update position based on input
                self.lift_position -= lift_input * 0.005  # Small position increment
                # Clamp lift position
                self.lift_position = max(0.0, min(1.0, self.lift_position))
                if self.motors['lift']:
                    self.motors['lift'].setPosition(self.lift_position)

            # Set wheel speeds
            for wheel in ['wheel1', 'wheel2', 'wheel3', 'wheel4']:
                if self.motors[wheel]:
                    self.motors[wheel].setVelocity(gantry_speed)

            # Set other motor speeds
            if self.motors['bridge']: self.motors['bridge'].setVelocity(bridge_speed)
            if self.motors['turret']: self.motors['turret'].setVelocity(turret_speed)

        except Exception as e:
            print(f"Movement error: {e}")
            self.stop_all_motors()

    def handle_grippers(self, buttons):
        """Original gripper logic"""
        try:
            if buttons.get('a', False):  # Open
                for gripper in self.grippers.values():
                    if gripper:
                        gripper.setPosition(GRIPPER_OPEN)
            elif buttons.get('b', False):  # Close
                for gripper in self.grippers.values():
                    if gripper:
                        gripper.setPosition(GRIPPER_CLOSE)
        except Exception as e:
            print(f"Gripper error: {e}")

    def stop_all_motors(self):
        # Stop movement motors
        for motor_name in ['wheel1', 'wheel2', 'wheel3', 'wheel4', 'bridge', 'turret']:
            if self.motors[motor_name]:
                self.motors[motor_name].setVelocity(0.0)
        
        # Keep lift at its current position
        if self.motors['lift']:
            self.motors['lift'].setPosition(self.lift_position)

    async def run(self):
        uri = "ws://localhost:3000"
        print("Starting controller...")
        
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    print("Connected to gamepad server")
                    
                    while self.robot.step(CONTROL_STEP) != -1:
                        try:
                            msg = await websocket.recv()
                            state = json.loads(msg)
                            self.handle_movement(state.get('axes', {}))
                            self.handle_grippers(state.get('buttons', {}))
                            
                        except websockets.exceptions.ConnectionClosed:
                            print("Connection lost, reconnecting...")
                            break
                        except Exception as e:
                            print(f"Error: {e}")
                            self.stop_all_motors()
                            
            except Exception as e:
                print(f"Connection error: {e}")
                self.stop_all_motors()
                await asyncio.sleep(1)

def main():
    controller = GantryController()
    asyncio.get_event_loop().run_until_complete(controller.run())

if __name__ == "__main__":
    main()