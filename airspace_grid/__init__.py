# airspace_grid/__init__.py
"""
iwhereGIS 网格数据引擎包
"""

from .grid_manager import AirspaceGridManager
from .grid_core import GridCell, GridGenerator
from .grid_encode import GridEncoder, encode_grid
from .grid_decode import decode_grid
from .grid_attributes import GridAttributes, GridAttributeManager

__version__ = "1.2.4"
__author__ = "iwhereGIS团队"

__all__ = [
    'AirspaceGridManager',
    'GridCell', 
    'GridGenerator',
    'GridEncoder',
    'encode_grid',
    'decode_grid',
    'GridAttributes',
    'GridAttributeManager'
] 