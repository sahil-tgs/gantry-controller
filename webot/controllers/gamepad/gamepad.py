import asyncio
import websockets
import json
from controller import Robot, Motor

# Constants
TIME_STEP = 16
NUM_MOTORS = 12
NUM_STATES = 6

# Speed and position limits
FRONT = +0.7  # For hip motors
BACK = -0.7   # For hip motors
HI = +0.02    # For knee motors
LO = -0.02    # For knee motors

# Motor names in the hexapod
MOTOR_NAMES = ["hip_motor_l0", "hip_motor_l1", "hip_motor_l2", "hip_motor_r0",
               "hip_motor_r1", "hip_motor_r2", "knee_motor_l0", "knee_motor_l1",
               "knee_motor_l2", "knee_motor_r0", "knee_motor_r1", "knee_motor_r2"]

# Gait positions (your existing position arrays)
pos_hip_forward = [
    [BACK, FRONT, BACK, -FRONT, -BACK, -FRONT],  # State 0
    [BACK, FRONT, BACK, -FRONT, -BACK, -FRONT],  # State 1
    [BACK, FRONT, BACK, -FRONT, -BACK, -FRONT],  # State 2
    [FRONT, BACK, FRONT, -BACK, -FRONT, -BACK],  # State 3
    [FRONT, BACK, FRONT, -BACK, -FRONT, -BACK],  # State 4
    [FRONT, BACK, FRONT, -BACK, -FRONT, -BACK],  # State 5
]

pos_hip_backward = [
    [FRONT, BACK, FRONT, -BACK, -FRONT, -BACK],  # State 5
    [FRONT, BACK, FRONT, -BACK, -FRONT, -BACK],  # State 4
    [FRONT, BACK, FRONT, -BACK, -FRONT, -BACK],  # State 3
    [BACK, FRONT, BACK, -FRONT, -BACK, -FRONT],  # State 2
    [BACK, FRONT, BACK, -FRONT, -BACK, -FRONT],  # State 1
    [BACK, FRONT, BACK, -FRONT, -BACK, -FRONT],  # State 0
]

pos_knee = [
    [LO, HI, LO, HI, LO, HI],  # State 0
    [HI, HI, HI, HI, HI, HI],  # State 1
    [HI, LO, HI, LO, HI, LO],  # State 2
    [HI, LO, HI, LO, HI, LO],  # State 3
    [HI, HI, HI, HI, HI, HI],  # State 4
    [LO, HI, LO, HI, LO, HI],  # State 5
]

pos_hip_right_turn = [
    [FRONT, FRONT, BACK, -BACK, -FRONT, -FRONT],  # State 0
    [FRONT, FRONT, BACK, -BACK, -FRONT, -FRONT],  # State 1
    [BACK, BACK, FRONT, -FRONT, -BACK, -BACK],    # State 2
    [BACK, BACK, FRONT, -FRONT, -BACK, -BACK],    # State 3
    [FRONT, FRONT, BACK, -BACK, -FRONT, -FRONT],  # State 4
    [BACK, BACK, FRONT, -FRONT, -BACK, -BACK],    # State 5
]

pos_hip_left_turn = [
    [BACK, BACK, FRONT, -FRONT, -BACK, -BACK],    # State 0
    [BACK, BACK, FRONT, -FRONT, -BACK, -BACK],    # State 1
    [FRONT, FRONT, BACK, -BACK, -FRONT, -FRONT],  # State 2
    [FRONT, FRONT, BACK, -BACK, -FRONT, -FRONT],  # State 3
    [BACK, BACK, FRONT, -FRONT, -BACK, -BACK],    # State 4
    [FRONT, FRONT, BACK, -BACK, -FRONT, -FRONT],  # State 5
]

pos_knee_turn = [
    [HI, HI, HI, HI, HI, HI],  # State 0
    [LO, HI, LO, HI, LO, HI],  # State 1
    [HI, LO, HI, LO, HI, LO],  # State 2
    [HI, HI, HI, HI, HI, HI],  # State 3
    [LO, HI, LO, HI, LO, HI],  # State 4
    [HI, LO, HI, LO, HI, LO],  # State 5
]

def clamp(value, min_value, max_value):
    """Clamp value between min and max"""
    return max(min(value, max_value), min_value)

class HexapodController:
    def __init__(self):
        # Initialize robot and motors
        self.robot = Robot()
        self.motors = [self.robot.getDevice(name) for name in MOTOR_NAMES]
        self.elapsed = 0

        # Set motors to position control mode
        for motor in self.motors:
            motor.setPosition(float('inf'))
            motor.setVelocity(0.0)

    def handle_movement(self, forward_back, left_right):
        # Calculate gait state based on time elapsed
        self.elapsed += 1
        state = (self.elapsed // 25) % NUM_STATES

        # Handle turning with higher priority than forward/backward
        if abs(left_right) > 0.1:
            # Calculate turn speed
            speed = clamp(abs(left_right) * 3.0, 0, 3.0)
            
            if left_right > 0:
                # Right turn
                for i in range(6):
                    self.motors[i].setPosition(clamp(pos_hip_right_turn[state][i], BACK, FRONT))
            else:
                # Left turn
                for i in range(6):
                    self.motors[i].setPosition(clamp(pos_hip_left_turn[state][i], BACK, FRONT))

            # Update knee motors for turning
            for i in range(6, 12):
                self.motors[i].setPosition(clamp(pos_knee_turn[state][i - 6], LO, HI))

            # Apply speed
            for i in range(NUM_MOTORS):
                self.motors[i].setVelocity(speed)

        else:
            # Handle forward/backward movement
            if forward_back < -0.1:
                # Backward movement
                for i in range(6):
                    self.motors[i].setPosition(clamp(pos_hip_backward[state][i], BACK, FRONT))
            elif forward_back > 0.1:
                # Forward movement
                for i in range(6):
                    self.motors[i].setPosition(clamp(pos_hip_forward[state][i], BACK, FRONT))

            # Update knee motors
            for i in range(6, 12):
                self.motors[i].setPosition(clamp(pos_knee[state][i - 6], LO, HI))

            # Apply speed based on input
            speed = clamp(abs(forward_back) * 3.0, 0, 3.0)
            for i in range(NUM_MOTORS):
                self.motors[i].setVelocity(speed)

    async def run(self):
        """Main control loop"""
        uri = "ws://localhost:3000"
        print(f"Connecting to WebSocket server at {uri}")
        
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    print("Connected to gamepad server")
                    
                    while self.robot.step(TIME_STEP) != -1:
                        try:
                            # Get gamepad state
                            msg = await websocket.recv()
                            state = json.loads(msg)
                            
                            # Get movement values from axes
                            forward_back = -state.get('axes', {}).get('left_y', 0)  # Inverted for correct direction
                            left_right = state.get('axes', {}).get('left_x', 0)
                            
                            # Handle movement
                            self.handle_movement(forward_back, left_right)
                            
                        except websockets.exceptions.ConnectionClosed:
                            print("Connection lost, reconnecting...")
                            break
                        except Exception as e:
                            print(f"Error in control loop: {e}")
                            continue
                            
            except Exception as e:
                print(f"Connection error: {e}")
                await asyncio.sleep(2)

def main():
    controller = HexapodController()
    asyncio.get_event_loop().run_until_complete(controller.run())

if __name__ == "__main__":
    main()