# airspace_grid/grid_encode.py
from enum import Enum
from typing import Dict, List, Tuple
import math
from decimal import Decimal, getcontext
from dataclasses import dataclass

# 设置足够精度处理小数
getcontext().prec = 24

MAX_ELEVATION = 1000  # 最大高程1000米
ELEVATION_BITS = 6   # 高程编码位数

class Hemisphere(Enum):
    NORTH = "North"
    SOUTH = "South"


class Quadrant(Enum):
    NE = "NE"  # North-East
    NW = "NW"  # North-West
    SE = "SE"  # South-East
    SW = "SW"  # South-West


@dataclass
class GridCell:
    level: int
    bbox: List[float]
    center: List[float]
    size: Dict[str, float]
    code: str = ""
    alt_range: Tuple[float, float] = (0, 1000)
    cellid: int = 0         # 网格ID

    def copy(self):
        return GridCell(
            level=self.level,
            bbox=self.bbox.copy(),
            center=self.center.copy(),
            size=self.size.copy(),
            code=self.code,
            alt_range=self.alt_range,
            cellid=self.cellid
        )


class GridEncoder:
    """空域网格编码器（三维增强版）"""
    MAX_ELEVATION = 1000  # 最大高程1000米
    ELEVATION_BITS = 6   # 高程编码位数
    
    @staticmethod
    def get_hemisphere(lat: float) -> str:
        return 'N' if lat >= 0 else 'S'
    
    @staticmethod
    def encode_level1(lon: float, lat: float) -> Tuple[str, str]:
        """第一级网格编码
            网格定义：全球按6°(经)×4°(纬)划分
            共60个经度区×45个纬度区
            赤道处约668km×444km
            
        Args:
            lon: 经度[-180,180]
            lat: 纬度[-90,90]
        
        Returns:
            tuple: (经度区号(01-60), 纬度区号(A-X))
        """
        # 边界处理
        if lon == 180:
            lon = -180
        if lat == 90:
            lat_idx = 22
        else:
            lat_idx = int(abs(lat) // 4)
        
        lon_idx = int((lon + 180) // 6) + 1
        lat_char = chr(ord('A') + lat_idx)
        
        return f"{lon_idx:02d}", lat_char


    @staticmethod 
    def encode_level2(lon: float, lat: float) -> str:
        """第二级网格编码
            网格定义：将6°*4°网格6*4划分
            得到3°*2°网格单元
            赤道处约384km×256km      
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            (半球标识, 网格编码)
        """
        # 判断半球
        hemisphere = ""
        if lon < 0 and lat >= 0:
            hemisphere = "NW"  # 西北半球
        elif lon >= 0 and lat >= 0:
            hemisphere = "NE"  # 东北半球
        elif lon < 0 and lat < 0:
            hemisphere = "SW"  # 西南半球
        else:
            hemisphere = "SE"  # 东南半球
        
        # 计算第二级网格索引
        lon_idx = int(abs(lon) // 3)
        lat_idx = int(abs(lat) // 2)
        
        # Z序编码
        if hemisphere == "NW":
            code = (lat_idx % 2) * 2 + (lon_idx % 2)
        elif hemisphere == "NE":
            code = (lat_idx % 2) * 2 + (1 - (lon_idx % 2))
        elif hemisphere == "SW":
            code = (1 - (lat_idx % 2)) * 2 + (lon_idx % 2)
        else:  # SE
            code = (1 - (lat_idx % 2)) * 2 + (1 - (lon_idx % 2))
        return f"{code}"  

    @staticmethod 
    def encode_level3(lon: float, lat: float) -> Tuple[str, str]:
        """第三级网格编码（第6、7位码元）
            网格定义：将3°*2°网格6*4划分
            得到30'*30'网格单元
            赤道处约55.66km×55.66km      
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            (经度编码, 纬度编码)
        """
        # 1. 计算当前经纬度在第三级网格内的余数（30'=0.5°）
        lon_remain = abs(lon) % 3  # 经度余数（0~3°）
        lat_remain = abs(lat) % 2  # 纬度余数（0~2°）
        
        # 2. 转换为0~5（经度）和0~3（纬度）的索引
        lon_idx = int(lon_remain // 0.5)  # 每0.5°一格，共6格
        lat_idx = int(lat_remain // 0.5)  # 每0.5°一格，共4格
        
        # 3. 根据半球调整索引顺序
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            return (f"{5 - lon_idx}" , f"{3 - lat_idx}")
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            return (f"{lon_idx}" , f"{3 - lat_idx}")
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            return (f"{5 - lon_idx}" , f"{lat_idx}" )
        else:                       # 东南半球（SE）
            return (f"{lon_idx}" , f"{lat_idx}" )
    
    @staticmethod 
    def encode_level4(lon: float, lat: float) -> str:
        """第四级网格编码（第8位码元）
            网格定义：将30'*30'网格2×3划分
            得到15'*10'网格单元
            赤道处约27.83km×27.83km        
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第四级网格编码（0~5）
        """
        # 1. 计算当前经纬度在第四级网格内的余数（15'=0.25°, 10'≈0.1667°）
        lon_remain = abs(lon) % 0.5  # 在30'网格内再分2份
        lat_remain = abs(lat) % 0.5  # 在30'网格内再分3份
        
        # 2. 转换为行列索引
        col = 0 if lon_remain < 0.25 else 1  # 经度方向（0=左, 1=右）
        row = int(lat_remain // (1/6))       # 纬度方向（0=顶部, 1=中部, 2=底部）
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [5, 4], [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [4, 5], [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2], [5, 4] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3], [4, 5] ]
        
        return f"{z_table[row][col]}"

    
    @staticmethod 
    def encode_level5(lon: float, lat: float) -> str:
        """第五级网格编码（第9位码元）
            网格定义：将15'*10'网格3×2划分
            得到5'*5'网格单元
            赤道处约9.27km×9.27km           
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第五级网格编码（0~5）
        """
        # 1. 计算当前经纬度在第五级网格内的余数（5'≈0.0833°）
        lon_remain = abs(lon) % 0.25  # 在15'网格内再分3份
        lat_remain = abs(lat) % 0.1667  # 在10'网格内再分2份
        
        # 2. 转换为行列索引
        col = int(lon_remain // (0.25/3))  # 经度方向（0=左, 1=中, 2=右）
        row = 0 if lat_remain < 0.0833 else 1  # 纬度方向（0=上, 1=下）
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [5, 3, 4], [2, 1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [3, 5, 4], [0, 1, 2] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [2, 0, 1], [5, 3, 4] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 2, 1], [3, 5, 4] ]
        
        return f"{z_table[row][col]}"
    
    @staticmethod 
    def encode_level6(lon: float, lat: float) -> Tuple[str, str]:
        """第六级网格编码（第10、11位码元）
            网格定义：将5'*5'网格5×5划分
            得到1'*1'网格单元
            赤道处约1.85km×1.85km    
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            (经度编码, 纬度编码)
        """
        # 1. 计算当前经纬度在第六级网格内的余数（1'≈0.0167°）
        lon_remain = abs(lon) % (5/60)  # 5'网格内再分5份
        lat_remain = abs(lat) % (5/60)
        
        # 2. 转换为0~4的索引（每1'一格）
        col = int(lon_remain // (1/60))  # 经度方向（0~4）
        row = int(lat_remain // (1/60))  # 纬度方向（0~4）
        
        # 3. 根据半球调整索引顺序
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            return (f"{4 - col}", f"{4 - row}")
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            return (f"{col}", f"{4 - row}")
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            return (f"{4 - col}", f"{row}")
        else:                       # 东南半球（SE）
            return (f"{col}", f"{row}")    

    @staticmethod 
    def encode_level7(lon: float, lat: float) -> Tuple[str, str]:
        """第七级网格编码（第13、14位码元）
            网格定义：将1'*1'网格5×5划分
            得到12”*12"网格单元
            赤道处约371.06m×371.06m    
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            (经度编码, 纬度编码)
        """
        # 1. 计算当前经纬度在第七级网格内的余数（12"=0.00333°）
        lon_remain = abs(lon) % (1/60)  # 1'网格内再分5份
        lat_remain = abs(lat) % (1/60)
        
        # 2. 转换为0~4的索引（每12"一格）
        col = int(lon_remain // (12/3600))  # 经度方向（0~4）
        row = int(lat_remain // (12/3600))  # 纬度方向（0~4）
        
        # 3. 根据半球调整索引顺序
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            return (f"{4 - col}", f"{4 - row}")
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            return (f"{col}", f"{4 - row}")
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            return (f"{4 - col}", f"{row}")
        else:                       # 东南半球（SE）
            return (f"{col}", f"{row}")


    @staticmethod 
    def encode_level8(lon: float, lat: float) -> str:
        """第八级网格编码（第16位码元）
            网格定义：将12"*12"网格3×3划分
            得到4”*4"网格单元
            赤道处约123.69m×123.69m            
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第八级网格编码（0~8）
        """
        # 1. 计算当前经纬度在第八级网格内的余数（4"≈0.00111°）
        lon_remain = abs(lon) % (12/3600)  # 12"网格内再分3份
        lat_remain = abs(lat) % (12/3600)
        
        # 2. 转换为行列索引（0=左/上，1=中，2=右/下）
        col = int(lon_remain // (4/3600))  # 经度方向（0~2）
        row = int(lat_remain // (4/3600))  # 纬度方向（0~2）
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [8, 6, 7], [5, 4, 3], [2, 1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [6, 8, 7], [3, 4, 5], [0, 1, 2] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [2, 0, 1], [5, 4, 3], [8, 6, 7] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 2, 1], [3, 4, 5], [6, 8, 7] ]
        
        return f"{z_table[row][col]}"


    @staticmethod
    def encode_level9(lon: float, lat: float) -> str:
        """第九级网格编码（第18位码元）
            网格定义：将4"*4"网格2×2划分
            得到2”*2"网格单元
            赤道处约61.84m×61.84m        
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第九级网格编码（0~3）
        """
        # 1. 计算当前经纬度在第九级网格内的余数（2"≈0.000555°）
        lon_remain = abs(lon) % (4/3600)  # 4"网格内再分2份
        lat_remain = abs(lat) % (4/3600)
        
        # 2. 转换为行列索引（0=左/上，1=右/下）
        col = 0 if lon_remain < (2/3600) else 1  # 经度方向
        row = 0 if lat_remain < (2/3600) else 1  # 纬度方向
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3] ]
        
        return f"{z_table[row][col]}"

    @staticmethod
    def encode_level10(lon: float, lat: float) -> str:
        """第十级网格编码（第20位码元）
            网格定义：将2"*2"的第十级网格2×2等分
            得到1"*1"的网格单元
            赤道处约30.9m×30.9m      
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第十级网格编码（0~3）
        """
        # 1. 计算当前经纬度在第十级网格内的余数（1"≈0.000277°）
        lon_remain = abs(lon) % (2/3600)  # 2"网格内再分2份
        lat_remain = abs(lat) % (2/3600)
        
        # 2. 转换为行列索引（0=左/上，1=右/下）
        col = 0 if lon_remain < (1/3600) else 1  # 经度方向
        row = 0 if lat_remain < (1/3600) else 1  # 纬度方向
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3] ]
        
        return f"{z_table[row][col]}"


    @staticmethod
    def encode_level11(lon: float, lat: float) -> str:
        """第十一级网格编码（第22位码元）
            网格定义：将1"*1"的第十级网格2×2等分
            得到1/2"*1/2"的网格单元
            赤道处约15.46m×15.46m       
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第十一级网格编码（0~3）
        """
        # 1. 计算当前经纬度在第十级网格内的余数（1"≈0.000277°）
        lon_remain = abs(lon) % (1/3600)  # 2"网格内再分2份
        lat_remain = abs(lat) % (1/3600)
        
        # 2. 转换为行列索引（0=左/上，1=右/下）
        col = 0 if lon_remain < (0.5/3600) else 1  # 经度方向
        row = 0 if lat_remain < (0.5/3600) else 1  # 纬度方向
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3] ]
        
        return f"{z_table[row][col]}"

    @staticmethod
    def encode_level12(lon: float, lat: float) -> str:
        """第十二级网格编码（第24位码元）
            网格定义：将1/2"*1/2"网格2×2划分
            得到1/4”*1/4"网格单元
            赤道处约7.73m×7.73m
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第十二级网格编码（0~3）
        """
        # 1. 计算当前经纬度在第十级网格内的余数（1"≈0.000277°）
        lon_remain = abs(lon) % (0.5/3600)  # 2"网格内再分2份
        lat_remain = abs(lat) % (0.5/3600)
        
        # 2. 转换为行列索引（0=左/上，1=右/下）
        col = 0 if lon_remain < (0.25/3600) else 1  # 经度方向
        row = 0 if lat_remain < (0.25/3600) else 1  # 纬度方向
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3] ]
        
        return f"{z_table[row][col]}"

    @staticmethod
    def encode_level13(lon: float, lat: float) -> str:
        """第十三级网格编码（第26位码元）
            网格定义：将1/4"*1/4"网格2×2划分
            得到1/8”*1/8"网格单元
            赤道处约3.86m×3.86m
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第十级网格编码（0~3）
        """
        # 1. 计算当前经纬度在第十级网格内的余数（1"≈0.000277°）
        lon_remain = abs(lon) % (0.25/3600)  # 2"网格内再分2份
        lat_remain = abs(lat) % (0.25/3600)
        
        # 2. 转换为行列索引（0=左/上，1=右/下）
        col = 0 if lon_remain < (0.125/3600) else 1  # 经度方向
        row = 0 if lat_remain < (0.125/3600) else 1  # 纬度方向
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3] ]
        
        return f"{z_table[row][col]}"
    

    @staticmethod
    def encode_level14(lon: float, lat: float) -> str:
        """第十四级网格编码（第28位码元）
            网格定义：将1/8"*1/8"网格2×2划分
            得到1/16”*1/16"网格单元
            赤道处约1.93m×1.93m
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第十四级网格编码（0~3）
        """
        # 1. 计算当前经纬度在第十级网格内的余数（1"≈0.000277°）
        lon_remain = abs(lon) % (0.125/3600)  # 2"网格内再分2份
        lat_remain = abs(lat) % (0.125/3600)
        
        # 2. 转换为行列索引（0=左/上，1=右/下）
        col = 0 if lon_remain < (0.0625/3600) else 1  # 经度方向
        row = 0 if lat_remain < (0.0625/3600) else 1  # 纬度方向
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3] ]
        
        return f"{z_table[row][col]}"

    @staticmethod
    def encode_level15(lon: float, lat: float) -> str:
        """第十五级网格编码（第30位码元）
            网格定义：将1/16"*1/16"网格2×2划分
            得到1/32”*1/32"网格单元
            赤道处约0.97m×0.97m
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第十五级网格编码（0~3）
        """
        # 1. 计算当前经纬度在第十级网格内的余数（1"≈0.000277°）
        lon_remain = abs(lon) % (0.0625/3600)  # 2"网格内再分2份
        lat_remain = abs(lat) % (0.0625/3600)
        
        # 2. 转换为行列索引（0=左/上，1=右/下）
        col = 0 if lon_remain < (0.03125/3600) else 1  # 经度方向
        row = 0 if lat_remain < (0.03125/3600) else 1  # 纬度方向
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3] ]
        
        return f"{z_table[row][col]}"
    
    @staticmethod
    def encode_level16(lon: float, lat: float) -> str:
        """第十六级网格编码（第32位码元）
            网格定义：将1/32"*1/32"网格2×2划分
            得到1/64”*1/64"网格单元
            赤道处约0.48m×0.48m
        Args:
            lon: 经度（-180° ~ 180°）
            lat: 纬度（-90° ~ 90°）
        
        Returns:
            第十六级网格编码（0~3）
        """
        # 1. 计算当前经纬度在第十级网格内的余数（1"≈0.000277°）
        lon_remain = abs(lon) % (0.03125/3600)  # 2"网格内再分2份
        lat_remain = abs(lat) % (0.03125/3600)
        
        # 2. 转换为行列索引（0=左/上，1=右/下）
        col = 0 if lon_remain < (0.015625/3600) else 1  # 经度方向
        row = 0 if lat_remain < (0.015625/3600) else 1  # 纬度方向
        
        # 3. 根据半球选择Z序表
        if lon < 0 and lat >= 0:    # 西北半球（NW）
            z_table = [ [3, 2], [1, 0] ]
        elif lon >= 0 and lat >= 0: # 东北半球（NE）
            z_table = [ [2, 3], [0, 1] ]
        elif lon < 0 and lat < 0:   # 西南半球（SW）
            z_table = [ [1, 0], [3, 2] ]
        else:                       # 东南半球（SE）
            z_table = [ [0, 1], [2, 3] ]
        
        return f"{z_table[row][col]}"

    @classmethod
    def generate_code(self, lon: float, lat: float, height: float = 0, level: int = 1) -> str:
        """生成三维网格编码"""
        code_parts = []
        #1. 半球标识
        code_parts.append(self.get_hemisphere(lat))  #获取南北半球
        
        # 2-4. 第一级网格
        num_twoThreeCode, num_fourCode = self.encode_level1(lon, abs(lat))

        # 5. 第二级网格
        num_fiveCode = self.encode_level2(lon,lat)
       
        # 6~7. 第三级网格
        num_sixCode,num_sevenCode = self.encode_level3(lon,lat)

        # 8. 第四级网格
        num_eightCode = self.encode_level4(lon,lat)

        # 9. 第五级网格
        num_nineCode = self.encode_level5(lon,lat)

        #10~11. 第六级网格
        num_tenCode,num_elevenCode = self.encode_level6(lon,lat)

        # 13~14. 第七级网格
        num_thirteenCode,num_fourteenCode = self.encode_level7(lon,lat)

        # 16. 第八级网格
        num_sixteenCode = self.encode_level8(lon,lat)

        # 18. 第九级网格
        num_eighteenCode = self.encode_level9(lon,lat)

        # 20. 第十级网格
        num_twentyCode = self.encode_level10(lon,lat)

        # 22. 第十一级网格
        num_twentyTwoCode = self.encode_level11(lon,lat)

        # 24. 第十二级网格
        num_twentyFourCode = self.encode_level12(lon,lat)

        # 26. 第十三级网格
        num_twentySixCode = self.encode_level13(lon,lat)

        # 28. 第十四级网格
        num_twentyEightCode = self.encode_level14(lon,lat)

        # 30. 第十五级网格
        num_thirtyCode = self.encode_level15(lon,lat)
       
        # 32. 第十六级网格
        num_thirtyTwoCode = self.encode_level16(lon,lat)

        code_parts.extend([num_twoThreeCode, num_fourCode,num_fiveCode,
                           num_sixCode,num_sevenCode,num_eightCode,
                           num_nineCode,num_tenCode,num_elevenCode,
                           num_thirteenCode,num_fourteenCode,num_sixteenCode,
                           num_eighteenCode,num_twentyCode,num_twentyTwoCode,num_twentyFourCode,
                           num_twentySixCode,num_twentyEightCode,num_thirtyCode,num_thirtyTwoCode
                           ])
        code_str = ''.join(code_parts)
        code_list = list(code_str)
        # 当级别≥11时插入高程编码
        if level >= 6:
            elev_code = self.encode_elevation(height)
            # 定义高程编码应插入的准确位置
            elev_positions = [12, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33]
            for i, bit in enumerate(elev_code):
                if i >= len(elev_positions):
                    break  # 防止高程编码位数超过预定位置
                pos = elev_positions[i]
                # 确保位置不超过当前长度，否则填充至该位置
                while pos > (len(code_list)+1):
                    code_list.append('0')  # 用默认值填充空缺，或根据需求调整
                code_list.insert(pos, bit)

            final_code = ''.join(code_list)
        else:
            final_code = code_str
        return final_code
    
    @classmethod
    def encode_elevation(cls, elevation: float) -> str:
        """按照分层规则将高程编码为11位数字字符串"""
        # 将输入高程转换为Decimal处理，避免浮点误差
        try:
            elevation_dec = Decimal(str(elevation))
        except:
            raise ValueError("无效的高程值")

        # 验证高程范围
        if elevation_dec < 0 or elevation_dec > 1000:
            raise ValueError("高程超出范围 (0-1000米)")

        code = []
        current_lower = Decimal('0')
        current_upper = Decimal('1000')

        for _ in range(11):
            # 计算当前层级参数
            interval = current_upper - current_lower
            sub_interval = interval / 10
            
            # 计算当前子区间编号 (处理边界情况)
            offset = elevation_dec - current_lower
            epsilon = Decimal('1e-15')  # 微小偏移防止上界溢出
            safe_offset = offset - epsilon
            
            # 确定子区间索引
            index = (safe_offset // sub_interval).to_integral_exact()
            index = max(0, min(int(index), 9))  # 约束到0-9范围
            
            code.append(str(index))
            
            # 更新下一层区间边界
            current_lower, current_upper = (
                current_lower + index * sub_interval,
                current_lower + (index + 1) * sub_interval
            )

        return ''.join(code)


# 简化的函数接口，与TypeScript版本保持一致
def encode_grid(lon: float, lat: float, height: float = 0, level: int = 6) -> str:
    """编码函数"""
    encoder = GridEncoder()
    return encoder.generate_code(lon, lat, height, level)



