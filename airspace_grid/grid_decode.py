from enum import Enum
from typing import Dict, List, Tuple
import math
import re


class Hemisphere(Enum):
    NORTH = "North"
    SOUTH = "South"


class Quadrant(Enum):
    NE = "NE"  # North-East
    NW = "NW"  # North-West
    SE = "SE"  # South-East
    SW = "SW"  # South-West


class GridDecodeResult:
    """网格解码结果"""
    
    def __init__(self):
        self.level: int = 0
        self.bounds: Dict[str, float] = {
            'min_lon': 0,
            'max_lon': 0,
            'min_lat': 0,
            'max_lat': 0
        }
        self.center: List[float] = [0, 0]
        self.alt_range: List[float] = [0, 1000]
        self.lon_step: float = 0
        self.lat_step: float = 0
        self.code: str = ""


class GridDecoder:
    """
    空域网格解码器
    将网格编码逆向转换为空间信息
    """
    
    def __init__(self):
        self.MAX_ELEVATION = 1000.0  # 最大高度（米）
    
    def _get_level_from_length(self, length: int) -> int:
        """根据编码长度获取网格层级"""
        if length == 4:
            return 1  # N00A
        elif length == 5:
            return 2  # N00A0
        elif length == 7:
            return 3  # N00A000
        elif length == 8:
            return 4  # N00A0000
        elif length == 9:
            return 5  # N00A00000
        elif length == 12:
            return 6  # N00A00000000 (包含高度)
        elif length == 15:
            return 7  # Level 7
        elif length == 17:
            return 8  # Level 8
        else:
            # Level 9-16: 每级增加2个字符
            if 19 <= length <= 33 and (length - 17) % 2 == 0:
                return 8 + (length - 17) // 2
            raise ValueError(f"Invalid code length: {length}")
    
    def decode(self, code: str) -> GridDecodeResult:
        """解码网格编码"""
        if not code or len(code) < 4:
            raise ValueError("Invalid grid code")
        
        level = self._get_level_from_length(len(code))
        result = GridDecodeResult()
        result.level = level
        result.alt_range = [0, self.MAX_ELEVATION]
        result.code = code
        
        cursor = 0
        
        # 1. 解析半球
        hemisphere_char = code[cursor]
        cursor += 1
        if hemisphere_char not in ["N", "S"]:
            raise ValueError("Invalid hemisphere indicator")
        hemisphere = Hemisphere.NORTH if hemisphere_char == "N" else Hemisphere.SOUTH
        
        # 2. 解析Level 1 - 经纬度基础网格
        lon_idx_str = code[cursor:cursor + 2]
        cursor += 2
        
        # 验证经度字符是否为数字
        if not re.match(r'^\d{2}$', lon_idx_str):
            raise ValueError("Invalid longitude format - must be 2 digits")
        
        lon_idx = int(lon_idx_str)
        if lon_idx < 1 or lon_idx > 60:
            raise ValueError("Invalid longitude index - must be between 01 and 60")
        
        lat_char = code[cursor]
        cursor += 1
        
        # 验证纬度字符是否为有效字母
        if not re.match(r'^[A-Z]$', lat_char):
            raise ValueError("Invalid latitude format - must be a single uppercase letter")
        
        lat_idx = ord(lat_char) - ord('A')
        if lat_idx < 0 or lat_idx > 22:
            raise ValueError("Invalid latitude character - must be between A and W")
        
        # 计算Level 1的边界
        result.bounds['min_lon'] = -180.0 + (lon_idx - 1) * 6.0
        result.bounds['max_lon'] = result.bounds['min_lon'] + 6.0
        
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = lat_idx * 4.0
            result.bounds['max_lat'] = result.bounds['min_lat'] + 4.0
        else:
            result.bounds['max_lat'] = -(lat_idx * 4.0)
            result.bounds['min_lat'] = result.bounds['max_lat'] - 4.0
        
        # 初始化中心点和步长
        result.center = [
            (result.bounds['min_lon'] + result.bounds['max_lon']) / 2,
            (result.bounds['min_lat'] + result.bounds['max_lat']) / 2
        ]
        result.lon_step = result.bounds['max_lon'] - result.bounds['min_lon']
        result.lat_step = result.bounds['max_lat'] - result.bounds['min_lat'] 
       
        # Level 2: 2x2子分区
        if level >= 2 and cursor < len(code):
            l2_code = int(code[cursor])
            cursor += 1
            self._refine_level2(result, l2_code, hemisphere)
        
        # Level 3: 6x4子分区
        if level >= 3 and cursor + 1 < len(code):
            l3_lon_idx = int(code[cursor])
            cursor += 1
            l3_lat_idx = int(code[cursor])
            cursor += 1
            self._refine_level3(result, l3_lon_idx, l3_lat_idx, hemisphere)
        
        # Level 4: 3x2子分区
        if level >= 4 and cursor < len(code):
            l4_code = int(code[cursor])
            cursor += 1
            self._refine_level4(result, l4_code, hemisphere)
        
        # Level 5: 2x3子分区
        if level >= 5 and cursor < len(code):
            l5_code = int(code[cursor])
            cursor += 1
            self._refine_level5(result, l5_code, hemisphere)
        
        # Level 6: 5x5子分区 + 高度
        if level >= 6 and cursor + 2 < len(code):
            l6_lon_idx = int(code[cursor])
            cursor += 1
            l6_lat_idx = int(code[cursor])
            cursor += 1
            l6_alt_code = int(code[cursor])
            cursor += 1
            self._refine_level6(result, l6_lon_idx, l6_lat_idx, l6_alt_code, hemisphere)
        
        # Level 7: 5x5子分区 + 高度
        if level >= 7 and cursor + 2 < len(code):
            l7_lon_idx = int(code[cursor])
            cursor += 1
            l7_lat_idx = int(code[cursor])
            cursor += 1
            l7_alt_code = int(code[cursor])
            cursor += 1
            self._refine_level7(result, l7_lon_idx, l7_lat_idx, l7_alt_code, hemisphere)
        
        # Level 8: 3x3子分区 + 高度
        if level >= 8 and cursor + 1 < len(code):
            l8_code = int(code[cursor])
            cursor += 1
            l8_alt_code = int(code[cursor])
            cursor += 1
            self._refine_level8(result, l8_code, l8_alt_code, hemisphere)
        
        # Level 9-16: 2x2子象限 + 高度
        for l in range(9, level + 1):
            if cursor + 1 < len(code):
                l_code = int(code[cursor])
                cursor += 1
                l_alt_code = int(code[cursor])
                cursor += 1
                self._refine_sub_quad(result, l_code, l_alt_code, l, hemisphere)
        
        # 计算中心点和步长
        result.center = [
            (result.bounds['min_lon'] + result.bounds['max_lon']) / 2.0,
            (result.bounds['min_lat'] + result.bounds['max_lat']) / 2.0
        ]
        result.lon_step = result.bounds['max_lon'] - result.bounds['min_lon']
        result.lat_step = abs(result.bounds['max_lat'] - result.bounds['min_lat'])
        
        return result
    
    def _refine_level2(self, result: GridDecodeResult, code: int, hemisphere: Hemisphere):
        """细化Level 2边界（2x2子分区）"""
        lon_span = (result.bounds['max_lon'] - result.bounds['min_lon']) / 2.0
        lat_span = abs(result.bounds['max_lat'] - result.bounds['min_lat']) / 2.0
        
        # 根据Z-order编码确定实际的行列
        quadrant = self._get_quadrant_from_bounds(result.bounds)
        col, row = self._decode_z_order_2x2(code, quadrant)
        
        # 更新经度边界
        result.bounds['min_lon'] = result.bounds['min_lon'] + col * lon_span
        result.bounds['max_lon'] = result.bounds['min_lon'] + lon_span
        
        # 更新纬度边界
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = result.bounds['min_lat'] + row * lat_span
            result.bounds['max_lat'] = result.bounds['min_lat'] + lat_span
        else:
            result.bounds['max_lat'] = result.bounds['max_lat'] - row * lat_span
            result.bounds['min_lat'] = result.bounds['max_lat'] - lat_span
    
    def _refine_level3(self, result: GridDecodeResult, lon_idx: int, lat_idx: int, hemisphere: Hemisphere):
        """细化Level 3边界（6x4子分区）"""
        lon_span = (result.bounds['max_lon'] - result.bounds['min_lon']) / 6.0
        lat_span = abs(result.bounds['max_lat'] - result.bounds['min_lat']) / 4.0
        
        # 直接使用索引，与简化后的编码器保持一致
        # 更新经度边界
        result.bounds['min_lon'] = result.bounds['min_lon'] + lon_idx * lon_span
        result.bounds['max_lon'] = result.bounds['min_lon'] + lon_span
        
        # 更新纬度边界
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = result.bounds['min_lat'] + lat_idx * lat_span
            result.bounds['max_lat'] = result.bounds['min_lat'] + lat_span
        else:
            result.bounds['max_lat'] = result.bounds['max_lat'] - lat_idx * lat_span
            result.bounds['min_lat'] = result.bounds['max_lat'] - lat_span
    
    def _refine_level4(self, result: GridDecodeResult, code: int, hemisphere: Hemisphere):
        """细化Level 4边界（3x2子分区）"""
        lon_span = (result.bounds['max_lon'] - result.bounds['min_lon']) / 2.0
        lat_span = abs(result.bounds['max_lat'] - result.bounds['min_lat']) / 3.0
        
        # 直接基于行优先编码解码，与简化后的编码器保持一致
        # 2列3行：code = row * 2 + col
        col = code % 2
        row = code // 2
        
        # 更新经度边界
        result.bounds['min_lon'] = result.bounds['min_lon'] + col * lon_span
        result.bounds['max_lon'] = result.bounds['min_lon'] + lon_span
        
        # 更新纬度边界
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = result.bounds['min_lat'] + row * lat_span
            result.bounds['max_lat'] = result.bounds['min_lat'] + lat_span
        else:
            result.bounds['max_lat'] = result.bounds['max_lat'] - row * lat_span
            result.bounds['min_lat'] = result.bounds['max_lat'] - lat_span
    
    def _refine_level5(self, result: GridDecodeResult, code: int, hemisphere: Hemisphere):
        """细化Level 5边界（2x3子分区） 3列2行"""
        lon_span = (result.bounds['max_lon'] - result.bounds['min_lon']) / 3.0
        lat_span = abs(result.bounds['max_lat'] - result.bounds['min_lat']) / 2.0
        
        # 直接基于行优先编码解码，与简化后的编码器保持一致
        # 3列2行：code = row * 3 + col
        col = code % 3
        row = code // 3
        
        # 更新经度边界
        result.bounds['min_lon'] = result.bounds['min_lon'] + col * lon_span
        result.bounds['max_lon'] = result.bounds['min_lon'] + lon_span
        
        # 更新纬度边界
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = result.bounds['min_lat'] + row * lat_span
            result.bounds['max_lat'] = result.bounds['min_lat'] + lat_span
        else:
            result.bounds['max_lat'] = result.bounds['max_lat'] - row * lat_span
            result.bounds['min_lat'] = result.bounds['max_lat'] - lat_span 
   
    def _refine_level6(self, result: GridDecodeResult, lon_idx: int, lat_idx: int, alt_code: int, hemisphere: Hemisphere):
        """细化Level 6边界（5x5子分区 + 高度）"""
        lon_span = (result.bounds['max_lon'] - result.bounds['min_lon']) / 5.0
        lat_span = abs(result.bounds['max_lat'] - result.bounds['min_lat']) / 5.0
        
        # 直接使用索引，与简化后的编码器保持一致
        # 更新经度边界
        result.bounds['min_lon'] = result.bounds['min_lon'] + lon_idx * lon_span
        result.bounds['max_lon'] = result.bounds['min_lon'] + lon_span
        
        # 更新纬度边界
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = result.bounds['min_lat'] + lat_idx * lat_span
            result.bounds['max_lat'] = result.bounds['min_lat'] + lat_span
        else:
            result.bounds['max_lat'] = result.bounds['max_lat'] - lat_idx * lat_span
            result.bounds['min_lat'] = result.bounds['max_lat'] - lat_span
        
        # 解析高度范围
        alt_step = self.MAX_ELEVATION / 2.0
        result.alt_range = [alt_code * alt_step, (alt_code + 1) * alt_step]
    
    def _refine_level7(self, result: GridDecodeResult, lon_idx: int, lat_idx: int, alt_code: int, hemisphere: Hemisphere):
        """细化Level 7边界（5x5子分区 + 高度）"""
        lon_span = (result.bounds['max_lon'] - result.bounds['min_lon']) / 5.0
        lat_span = abs(result.bounds['max_lat'] - result.bounds['min_lat']) / 5.0
        
        # 直接使用索引，与简化后的编码器保持一致
        # 更新经度边界
        result.bounds['min_lon'] = result.bounds['min_lon'] + lon_idx * lon_span
        result.bounds['max_lon'] = result.bounds['min_lon'] + lon_span
        
        # 更新纬度边界
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = result.bounds['min_lat'] + lat_idx * lat_span
            result.bounds['max_lat'] = result.bounds['min_lat'] + lat_span
        else:
            result.bounds['max_lat'] = result.bounds['max_lat'] - lat_idx * lat_span
            result.bounds['min_lat'] = result.bounds['max_lat'] - lat_span
        
        # 解析高度范围 - Level 7的高度编码：在当前高度范围内进一步细分
        current_alt_min = result.alt_range[0]
        current_alt_max = result.alt_range[1]
        current_alt_span = current_alt_max - current_alt_min
        
        # 将当前高度范围分为2个子区间
        alt_div = current_alt_span / 2.0
        alt_min = current_alt_min + alt_code * alt_div
        alt_max = alt_min + alt_div
        result.alt_range = [alt_min, alt_max]
    
    def _refine_level8(self, result: GridDecodeResult, code: int, alt_code: int, hemisphere: Hemisphere):
        """细化Level 8边界（3x3子分区 + 高度）"""
        lon_span = (result.bounds['max_lon'] - result.bounds['min_lon']) / 3.0
        lat_span = abs(result.bounds['max_lat'] - result.bounds['min_lat']) / 3.0
        
        # 直接基于行优先编码解码，与简化后的编码器保持一致
        # 3x3：code = row * 3 + col
        col = code % 3
        row = code // 3
        
        # 更新经度边界
        result.bounds['min_lon'] = result.bounds['min_lon'] + col * lon_span
        result.bounds['max_lon'] = result.bounds['min_lon'] + lon_span
        
        # 更新纬度边界
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = result.bounds['min_lat'] + row * lat_span
            result.bounds['max_lat'] = result.bounds['min_lat'] + lat_span
        else:
            result.bounds['max_lat'] = result.bounds['max_lat'] - row * lat_span
            result.bounds['min_lat'] = result.bounds['max_lat'] - lat_span
        
        # 解析高度范围 - Level 8的高度编码：在当前高度范围内进一步细分
        current_alt_min = result.alt_range[0]
        current_alt_max = result.alt_range[1]
        current_alt_span = current_alt_max - current_alt_min
        
        # 将当前高度范围分为2个子区间
        alt_div = current_alt_span / 2.0
        alt_min = current_alt_min + alt_code * alt_div
        alt_max = alt_min + alt_div
        result.alt_range = [alt_min, alt_max]
    
    def _refine_sub_quad(self, result: GridDecodeResult, code: int, alt_code: int, level: int, hemisphere: Hemisphere):
        """细化Level 9-16边界（2x2子象限 + 高度）"""
        # Level 9-16都是在前一级确定的格子基础上分为2x2
        # 当前result.bounds应该是前一级确定的边界
        parent_lon_span = result.bounds['max_lon'] - result.bounds['min_lon']
        parent_lat_span = abs(result.bounds['max_lat'] - result.bounds['min_lat'])
        
        # 在前一级格子内分为2x2
        lon_span = parent_lon_span / 2.0
        lat_span = parent_lat_span / 2.0
        
        # 直接基于行优先编码解码，与简化后的编码器保持一致
        # 2x2：code = row * 2 + col
        col = code % 2
        row = code // 2
        
        # 更新经度边界
        result.bounds['min_lon'] = result.bounds['min_lon'] + col * lon_span
        result.bounds['max_lon'] = result.bounds['min_lon'] + lon_span
        
        # 更新纬度边界
        if hemisphere == Hemisphere.NORTH:
            result.bounds['min_lat'] = result.bounds['min_lat'] + row * lat_span
            result.bounds['max_lat'] = result.bounds['min_lat'] + lat_span
        else:
            result.bounds['max_lat'] = result.bounds['max_lat'] - row * lat_span
            result.bounds['min_lat'] = result.bounds['max_lat'] - lat_span
        
        # 解析高度范围 - Level 9-16的高度编码：在当前高度范围内进一步细分
        current_alt_min = result.alt_range[0]
        current_alt_max = result.alt_range[1]
        current_alt_span = current_alt_max - current_alt_min
        
        # 将当前高度范围分为2个子区间
        alt_div = current_alt_span / 2.0
        alt_min = current_alt_min + alt_code * alt_div
        alt_max = alt_min + alt_div
        result.alt_range = [alt_min, alt_max]
    
    def _get_quadrant_from_bounds(self, bounds: Dict[str, float]) -> Quadrant:
        """根据边界获取象限"""
        center_lon = (bounds['min_lon'] + bounds['max_lon']) / 2.0
        center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2.0
        
        if center_lon >= 0.0:
            return Quadrant.NE if center_lat >= 0.0 else Quadrant.SE
        else:
            return Quadrant.NW if center_lat >= 0.0 else Quadrant.SW
    
    def _decode_z_order_2x2(self, code: int, quadrant: Quadrant) -> Tuple[int, int]:
        """解码2x2 Z-order编码"""
        z_tables = {
            Quadrant.NE: [[0, 1], [2, 3]],
            Quadrant.NW: [[1, 0], [3, 2]],
            Quadrant.SE: [[2, 3], [0, 1]],
            Quadrant.SW: [[3, 2], [1, 0]]
        }
        
        table = z_tables[quadrant]
        for row in range(2):
            for col in range(2):
                if table[row][col] == code:
                    return (col, row)
        return (0, 0)


# 简化的函数接口，与TypeScript版本保持一致
def decode_grid(code: str) -> GridDecodeResult:
    """解码函数"""
    decoder = GridDecoder()
    return decoder.decode(code)