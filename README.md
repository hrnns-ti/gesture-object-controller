# Hand-Tracked 3D Object Controller

An interactive computer vision application for controlling 3D object rotation and scale using hand gestures. This application implements a comparison of **three numerical filtering methods** (Raw, Exponential Smoothing, and Kalman Filter) to demonstrate jitter reduction in real-time hand tracking.

## Project Overview

The application uses a webcam to detect the position of two hands:

- **Left Hand**: Controls **rotation** of the 3D object based on palm center movement
  - Mode 1 (Raw): Unfiltered tracking noise for visualization
  - Mode 2 (Smoothing): Exponential smoothing for smooth movement
  - Mode 3 (Kalman): Kalman Filter for optimal state estimation
  - Auto-resetting baseline every 1 second for intuitive control

- **Right Hand**: Controls **scale** of the object based on thumb-index finger distance
  - Minimum scale: 0.5x (cannot scale down further)
  - Maximum scale: Unlimited (scales up indefinitely)
  - Exponential smoothing for smooth scaling

## Technologies Used

- **Computer Vision**: OpenCV, cvzone (Hand Tracking Module)
- **Numerical Methods**: Kalman Filter, Exponential Smoothing
- **Graphics**: OpenGL/GLUT (PyOpenGL)
- **3D Models**: OBJ Loader with MTL material support, face normals, and lighting
- **Threading**: Multithreading for separation between video loop and rendering

## Project Structure

```
.
├── main.py                          # Main application script
├── models/
│   ├── Lowpoly_tree_sample.obj      # 3D model (OBJ format)
│   └── Lowpoly_tree_sample.mtl      # Material definition (MTL format)
├── src/
│   ├── __init__.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── base_tracker.py          # Base tracker class
│   │   ├── kalman_tracker.py        # Kalman Filter implementation
│   │   └── hand_controller.py       # Filter mode handler
│   └── rendering/
│       ├── __init__.py
│       ├── obj_loader.py            # OBJ & MTL parser
│       └── cube_renderer.py         # OpenGL renderer
└── README.md                        # This file
```

## Installation

### Prerequisites

- Python 3.7 or higher
- Webcam support
- GPU optional (for better performance)

### Install Dependencies

```bash
  pip install opencv-python cvzone numpy PyOpenGL PyOpenGL_accelerate
```

### Verify Installation

```bash
  python -c "import cv2, cvzone, OpenGL; print('All dependencies installed!')"
````

## Usage

### 1. Run the Application

```bash
  python main.py
```

### 2. Interface

Two windows will appear:

- **"Two-Hand Control"**: Webcam feed with debug information
- **"3D Object"**: OpenGL window displaying the controllable 3D model

### 3. Hand Gesture Controls

#### Left Hand (Rotation)

- Move palm **left/right** → object rotates around Y-axis
- Move palm **up/down** → object rotates around X-axis
- Blue line shows baseline (rotation reference point)
- Baseline automatically resets every 1 second

#### Right Hand (Scale)

- **Increase** distance between thumb and index finger → object scales up
- **Decrease** distance between thumb and index finger → object scales down
- Minimum: 0.5x, no maximum limit

### 4. Filter Mode Selection (Press in 3D Object Window)

| Key | Mode | Characteristics |
|-----|------|-----------------|
| **1** | RAW | Visible jitter for noise visualization |
| **2** | SMOOTHING | Exponential smoothing, smooth movement |
| **3** | KALMAN | Kalman Filter, optimal estimation |
| **Q** or **ESC** | Exit | Close application |

## Key Features

### 1. Dual-Hand Tracking
- Simultaneous detection of 2 hands with X-position priority
- 21-point landmark detection from cvzone HandTrackingModule

### 2. Three-Mode Filter Comparison

**Raw Mode**: Direct tracking without filtering
- Palm position mapped directly to rotation angles
- Noise amplification gain: 80.0 degrees per screen width
- Non-linear function (square root) to amplify small noise

**Smoothing Mode**: Exponential filtering
- α = 0.3 for delta movement smoothing
- Deadzone: 1.0 pixel for tremor suppression
- Momentum-free integration

**Kalman Mode**: State estimation
- Position prediction based on velocity model
- Adaptive correction based on measurement noise
- Optimal for natural movement tracking

### 3. Baseline Auto-Reset
- Baseline resets to current hand position every 1 second
- Enables continuous control without drift
- Visual countdown in video overlay

### 4. OBJ Model Loading
- Full support for OBJ format with MTL materials
- Automatic mesh centroid calculation for centered rotation
- Per-face lighting with normal vectors
- Multiple material support with RGB colors

### 5. Real-Time Visualization
- **Red dot**: Raw palm position
- **Green dot**: Filtered palm position
- **Blue dot**: Baseline reference point
- **Blue line**: Delta vector (baseline → current position)
- **Overlay info**: Rotation angles, scale factor, filter mode, reset timer

## Numerical Implementation

### Kalman Filter (Mode 3)

```
State: [x, y]  (2D position)
Measurement: [x_raw, y_raw]

Prediction: x_pred = F * x_prev
Correction: x = x_pred + K * (z - H * x_pred)
```

### Exponential Smoothing (Mode 2)

```
x_filtered = (1 - α) * x_prev + α * x_current
```

### Raw Mapping (Mode 1)

```
x_norm = (x - width/2) / (width/2)       # normalize to [-1, 1]
rot_y = sign(x_norm) * |x_norm|^0.5 * 80.0
```

## Configuration

Edit parameters in `main.py`:

```python
# Baseline reset interval (seconds)
baseline_interval = 1.0

# Filter mode (in HandTrackingController)
# 1=raw, 2=smoothing, 3=Kalman

# Scale control parameters
s_min = 0.5                      # minimum scale
d_min = 30.0                     # minimum finger distance (pixels)
k = 1.0 / (200.0 - d_min)        # scale sensitivity factor

# Smoothing factors
scale_alpha = 0.2                # scale exponential smoothing
rot_vector_alpha = 0.3           # rotation delta smoothing

# Raw mode gain
jitter_gain = 80.0               # amplitude for noise magnification
```

## Troubleshooting

### Webcam not detected

```bash
  # Check available devices
  python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### Hand detection inaccurate

- Improve lighting conditions
- Keep distance less than 1 meter from camera
- Lower detection threshold in HandDetector from 0.8 to 0.7

### OpenGL window not appearing

- Ensure GPU drivers are installed
- Try reducing window size in `glutInitWindowSize`
- Check for OpenGL support with: `python -c "import OpenGL; print(OpenGL.__version__)"`

### Kalman filter mode still shows jitter

- Increase Q matrix (process noise covariance) in `kalman_tracker.py`
- Or decrease R matrix (measurement noise covariance)

## Data Collection for Research/Thesis

Metrics you can extract for documentation:

1. **Visual Comparison**: Screen recordings of Mode 1 vs 2 vs 3
2. **Jitter Metrics**:
   - Standard deviation of palm position per frame
   - Frequency analysis (FFT) of tracking noise
3. **Computational Performance**:
   - FPS for each filter mode
   - CPU/GPU utilization per mode

## Performance Notes

- **Optimal FPS**: 30 FPS (1280x720 resolution)
- **Latency**: ~50-100ms (camera + processing + rendering)
- **Memory**: ~200-300 MB for hand tracking + OpenGL rendering
- **CPU Usage**: ~20-30% (single core) for video processing

## License

This project is free to use for academic and personal purposes.

## Future Improvements

- [ ] Multi-object control with gesture switching
- [ ] Hand pose classification for mode switching without keyboard
- [ ] Data logging for filter performance analysis
- [ ] 360-degree trackball rotation mode
- [ ] Custom model loading from file dialog
- [ ] Filter parameter tuning UI

## Developer Notes

This application was designed as an educational demonstration to understand Kalman Filters and numerical methods in computer vision. For production use, consider:

- Implementing GPU acceleration for hand detection
- Adding input validation and error handling
- Optimizing memory usage for longer sessions
- Supporting multiple camera sources

## Contact & Support

For questions, bug reports, or feature requests, please contact the developer or create an issue in the project repository.

---

**Last Updated**: December 2025 
**Version**: 2.0  
**Python Version**: 3.12
