# pyRSM: Synchrotron XRD Reciprocal Space Mapping Tool

A Python package for processing synchrotron X-ray diffraction data from 2D detectors, converting scan data into 3D reciprocal space maps (h,k,l coordinates) with interactive visualization capabilities. This package has been tested at multiple beamlines at APS, CLS, SSRL, and ESRF, in multiple soft X-ray and hard X-ray diffraction and scattering experiments.


## Features

- Load and process synchrotron XRD spec files with 2D detector images
- Convert detector coordinates to reciprocal space (h,k,l) using sample orientation matrix
- Generate 3D intensity grids from single or multiple scans
- Interactive 3D visualization of detector images in reciprocal space
- Animated slice viewing through h, k, or l directions
- Data rebinning for performance optimization
- Support for custom h,k,l ranges and grid resolutions

## Installation

### Prerequisites
```bash
pip install numpy xrayutilities silx plotly pillow vtk
```

### Install from source
```bash
git clone https://github.com/yourusername/pyRSM.git
cd pyRSM
pip install -e .
```

## Quick Start

```python
from pyRSM import load_convert, rsm_convert, visualize_det, h_slice

# Load and convert a single scan
imgs, qx, qy, qz = load_convert('your_file', scan_number=14)

# Visualize detector images in 3D reciprocal space
fig = visualize_det(imgs, qx, qy, qz, cscale=[10, 95], downscale=10)
fig.show()

# Generate 3D reciprocal space map from multiple scans
grid_data, coords = rsm_convert('your_file', [14, 15, 16], 
                               h_n=100, k_n=100, l_n=100)

# Visualize h-slices through the data
h_slice(grid_data, coords, logscale=True, title="H-slices")
```

## API Reference

### `load_convert(file_name, scan_num)`
Load a single scan and convert to reciprocal space coordinates.

**Parameters:**
- `file_name` (str): Spec file name (without .spec extension)
- `scan_num` (int): Scan number to load

**Returns:**
- `imgs` (ndarray): Normalized detector images (3D array: frames × height × width)
- `qx, qy, qz` (ndarray): Reciprocal space coordinates corresponding to each detector pixel

**Key Features:**
- Automatically normalizes images by ion chamber readings
- Loads sample orientation matrix (UB matrix) from spec file
- Extracts X-ray energy from scan header
- Handles both scanned and fixed motor positions
- Configures detector geometry (516×516 pixels, 28.38mm active area, 770mm distance)

### `rsm_convert(file_name, scan_list, h_n=50, k_n=50, l_n=50, return_imgs=False, hklrange=None)`
Convert single or multiple scans into a 3D reciprocal space grid.

**Parameters:**
- `file_name` (str): Spec file name (without .spec extension)
- `scan_list` (int or list): Single scan number or list of scan numbers
- `h_n, k_n, l_n` (int): Grid dimensions for output (default: 50×50×50)
- `return_imgs` (bool): If True, also returns detector images and coordinates
- `hklrange` (list): Custom h,k,l ranges as [[h_min,h_max], [k_min,k_max], [l_min,l_max]]

**Returns:**
- `grid_data` (ndarray): 3D intensity grid in reciprocal space
- `coords` (list): [h_coords, k_coords, l_coords] coordinate arrays
- `imgs, qx, qy, qz` (optional): Raw detector data if `return_imgs=True`

### `visualize_det(imgs, qx, qy, qz, cscale=[50, 99], downscale=20)`
Interactive 3D visualization of detector images in reciprocal space.

**Parameters:**
- `imgs` (ndarray): Detector images from `load_convert`
- `qx, qy, qz` (ndarray): Reciprocal space coordinates
- `cscale` (list): Color scale percentiles [min, max] (default: [50, 99])
- `downscale` (int): Rebinning factor to reduce data size for performance (default: 20)

**Returns:**
- `fig` (plotly.graph_objects.Figure): Interactive 3D plot with animation controls

**Features:**
- Frame-by-frame animation through scan points
- Play/pause controls
- Slider for manual frame selection
- Automatic data rebinning for smooth performance
- Fixed aspect ratio and axis ranges

### `h_slice(grid_data, coords, logscale=False, dichro=False, title=None, start=0, cscale=[50, 99])`
Interactive visualization of h-slices through the 3D reciprocal space data.

**Parameters:**
- `grid_data` (ndarray): 3D intensity grid from `rsm_convert`
- `coords` (list): Coordinate arrays [h_coords, k_coords, l_coords]
- `logscale` (bool): Use logarithmic color scale (default: False)
- `dichro` (bool): Enable dichroic signal visualization with symmetric colormap (default: False)
- `title` (str): Plot title (optional)
- `start` (int): Starting frame number for animation (default: 0)
- `cscale` (list): Color scale percentiles [min, max] (default: [50, 99])

**Features:**
- Animated slicing through h-direction
- Play/pause controls and frame slider
- Automatic colormap selection (viridis for normal data, RdBu for dichroic)
- Support for both linear and logarithmic intensity scaling

### `k_slice(grid_data, coords, logscale=False, dichro=False, title=None, start=0, cscale=[50, 99])`
Interactive visualization of k-slices through the 3D reciprocal space data.

**Parameters:**
- Same as `h_slice` but slices through k-direction

**Features:**
- Animated slicing through k-direction with same controls as h_slice

### `l_slice(grid_data, coords, logscale=False, dichro=False, title=None, start=0, cscale=[50, 99])`
Interactive visualization of l-slices through the 3D reciprocal space data.

**Parameters:**
- Same as `h_slice` but slices through l-direction

**Features:**
- Animated slicing through l-direction with same controls as h_slice

## File Structure

Your data should be organized as:
```
your_project/
├── your_file.spec          # Spec file with scan metadata
└── images/
    └── S001/               # Scan directories (simplified structure)
        ├── your_file_S001_00000.tif
        ├── your_file_S001_00001.tif
        └── ...
```

## Example Workflows

### Single Scan Visualization
```python
from pyRSM import load_convert, visualize_det

# Load scan data
imgs, qx, qy, qz = load_convert('sample_data', 14)

# Create interactive 3D visualization
fig = visualize_det(imgs, qx, qy, qz, 
                   cscale=[50, 98],    # Adjust contrast
                   downscale=15)       # Balance quality vs performance
fig.show()
```

### Multi-Scan Reciprocal Space Mapping
```python
from pyRSM import rsm_convert, h_slice, k_slice, l_slice

# Process multiple scans into high-resolution 3D grid
file_name = "sample_data"
scan_list = [10, 11, 12, 13, 14, 15]

# Create detailed reciprocal space map
grid_data, coords = rsm_convert(file_name, scan_list, 
                               h_n=150, k_n=150, l_n=150)

# Visualize different slice directions
h_slice(grid_data, coords, logscale=True, title="H-slices through RSM")
k_slice(grid_data, coords, logscale=True, title="K-slices through RSM")
l_slice(grid_data, coords, title="L-slices through RSM", cscale=[50, 99])
```

### Custom Range and Resolution
```python
# Custom h,k,l range for focused analysis
custom_range = [[-0.1, 0.1], [-0.1, 0.1], [2.9, 3.1]]
grid_data, coords = rsm_convert(file_name, scan_list,
                               h_n=100, k_n=100, l_n=100,
                               hklrange=custom_range)


## Technical Details

### Detector Configuration (different from experiment to experiment)
- **Detector**: 516×516 pixel area detector
- **Pixel size**: 55 μm
- **Distance**: 770mm from sample
- **Center Pixel**: (188, 146)

### Coordinate System (check beamline configuration)
- **Sample axes**: x+, z-, y+, z- rotation sequence
- **Detector axes**: x+, z- 
- **Reference vector**: [0,1,0] (surface normal)
- **Primary beam**: [0,0,1] direction

### Data Processing
- Automatic I0 normalization using ion chamber readings
- 3D gridding with configurable resolution
- Support for both measured and fixed motor positions

### Visualization Features
- **Colormaps**: viridis (standard), RdBu (dichroic signals)
- **Scaling**: Linear or logarithmic intensity scaling
- **Animation**: Smooth frame transitions with play/pause controls
- **Performance**: Automatic rebinning for large datasets

## Requirements

- Python >= 3.7
- numpy >= 1.18.0
- xrayutilities >= 1.7.0
- silx >= 1.0.0
- plotly >= 5.0.0
- pillow >= 8.0.0
- vtk >= 9.0.0

## Installation Notes

The package expects:
1. Standard Spec files from diffraction beamline
2. TIF image files organized by scan number
3. UB matrix stored in spec file sample section
4. X-ray energy in scan header (in unit of KeV)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{pyrsm,
  title={pyRSM: Synchrotron XRD Reciprocal Space Mapping Tool},
  author={Jiarui Li},
  year={2025},
  url={https://github.com/jiaruili1993/pyRSM}
}
```

## Support

For questions or issues, please contact: jiaruili@stanford.edu