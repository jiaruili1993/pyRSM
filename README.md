# pyRSM
A Python package for processing synchrotron X-ray diffraction data from 2D detectors, converting scan data into 3D reciprocal space maps (h,k,l coordinates) with visualization capabilities.

## Features

- Load and process synchrotron XRD spec files with 2D detector images
- Convert detector coordinates to reciprocal space (h,k,l) using sample orientation matrix
- Generate 3D intensity grids from multiple scans
- Interactive visualization with h-slice viewing
- Support for dichroic signal analysis
- Export capabilities for further analysis

## Installation

### Prerequisites
```bash
pip install numpy xrayutilities silx pandas plotly pillow pyevtk vtk
```

### Install from source
```bash
git clone https://github.com/yourusername/APS-RSM.git
cd APS-RSM
pip install -e .
```

## Quick Start

```python
from APS_rsm import load_convert, rsm_convert, h_slice

# Load and convert a single scan
imgs, qx, qy, qz = load_convert('your_file', scan_number=14)

# Generate 3D reciprocal space map from multiple scans
grid_data, coords = rsm_convert('your_file', [14, 15, 16], 
                               h_n=50, k_n=50, l_n=50)

# Visualize h-slices
h_slice(grid_data, coords, logscale=True, title="My RSM Data")
```

## API Reference

### `load_convert(file_name, scan_num)`
Load a single scan and convert to reciprocal space coordinates.

**Parameters:**
- `file_name` (str): Spec file name (without .spec extension)
- `scan_num` (int): Scan number to load

**Returns:**
- `imgs` (ndarray): Normalized detector images
- `qx, qy, qz` (ndarray): Reciprocal space coordinates

### `rsm_convert(file_name, scan_list, h_n=50, k_n=50, l_n=50, return_imgs=False, hklrange=None)`
Convert multiple scans into a 3D reciprocal space grid.

**Parameters:**
- `file_name` (str): Spec file name
- `scan_list` (int or list): Single scan or list of scan numbers
- `h_n, k_n, l_n` (int): Grid dimensions for output
- `return_imgs` (bool): Whether to return detector images
- `hklrange` (list): Custom h,k,l ranges [[h_min,h_max], [k_min,k_max], [l_min,l_max]]

**Returns:**
- `grid_data` (ndarray): 3D intensity grid
- `coords` (list): [h_coords, k_coords, l_coords]

### `h_slice(grid_data, coords, logscale=False, dichro=False, title=None, start=0, cscale=[50,99])`
Interactive visualization of h-slices through the 3D data.

**Parameters:**
- `grid_data` (ndarray): 3D intensity data
- `coords` (list): Coordinate arrays from rsm_convert
- `logscale` (bool): Use logarithmic color scale
- `dichro` (bool): Enable dichroic signal visualization
- `title` (str): Plot title
- `start` (int): Starting frame number
- `cscale` (list): Color scale percentiles [min, max]

## File Structure

Your data should be organized as:
```
your_project/
├── your_file.spec          # Spec file
└── images/
    └── your_file/
        └── S001/           # Scan directories
            ├── your_file_S001_00000.tif
            ├── your_file_S001_00001.tif
            └── ...
```

## Example Workflow

```python
import numpy as np
from APS_rsm import rsm_convert, h_slice

# Process multiple scans into reciprocal space
file_name = "sample_data"
scan_list = [10, 11, 12, 13, 14]

# Generate 3D grid with 100x100x100 voxels
grid_data, coords = rsm_convert(file_name, scan_list, 
                               h_n=100, k_n=100, l_n=100)

# Visualize with logarithmic scaling
h_slice(grid_data, coords, logscale=True, 
        title="Reciprocal Space Map", cscale=[10, 99.5])
```

## Requirements

- Python >= 3.7
- numpy
- xrayutilities
- silx
- pandas
- plotly
- pillow (PIL)
- pyevtk
- vtk

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{aps_rsm,
  title={APS-RSM: Synchrotron XRD Reciprocal Space Mapping Tool},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/APS-RSM}
}
```

## Acknowledgments

- Advanced Photon Source (APS) for synchrotron facilities
- xrayutilities library developers
- silx project for data handling capabilities

## Support

For questions or issues, please:
- Open an issue on GitHub
- Contact: your.email@institution.edu
```