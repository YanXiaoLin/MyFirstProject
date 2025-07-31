# airspace_grid/grid_attributes.py
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class GridAttributes:
    """网格属性数据类"""
    # 基础属性
    grid_code: str
    level: int
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    center: List[float]  # [lon, lat]
    alt_range: List[float]  # [min_alt, max_alt]
    
    # 六大类属性数据
    # 1. 飞行规则属性
    flight_rules: Dict[str, Any] = field(default_factory=dict)
    
    # 2. 空域状态属性
    airspace_status: Dict[str, Any] = field(default_factory=dict)
    
    # 3. 气象环境属性
    weather_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # 4. 风险评估属性
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    
    # 5. 管制权限属性
    control_authority: Dict[str, Any] = field(default_factory=dict)
    
    # 6. 动态更新属性
    dynamic_updates: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    created_time: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_attribute(self, category: str, key: str, value: Any) -> None:
        """更新指定类别的属性"""
        categories = {
            'flight_rules': self.flight_rules,
            'airspace_status': self.airspace_status,
            'weather_conditions': self.weather_conditions,
            'risk_assessment': self.risk_assessment,
            'control_authority': self.control_authority,
            'dynamic_updates': self.dynamic_updates
        }
        
        if category in categories:
            categories[category][key] = value
            self.last_updated = datetime.now()
        else:
            raise ValueError(f"Invalid category: {category}")
    
    def get_attribute(self, category: str, key: str) -> Any:
        """获取指定类别的属性值"""
        categories = {
            'flight_rules': self.flight_rules,
            'airspace_status': self.airspace_status,
            'weather_conditions': self.weather_conditions,
            'risk_assessment': self.risk_assessment,
            'control_authority': self.control_authority,
            'dynamic_updates': self.dynamic_updates
        }
        
        if category in categories:
            return categories[category].get(key)
        else:
            raise ValueError(f"Invalid category: {category}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'grid_code': self.grid_code,
            'level': self.level,
            'bbox': self.bbox,
            'center': self.center,
            'alt_range': self.alt_range,
            'flight_rules': self.flight_rules,
            'airspace_status': self.airspace_status,
            'weather_conditions': self.weather_conditions,
            'risk_assessment': self.risk_assessment,
            'control_authority': self.control_authority,
            'dynamic_updates': self.dynamic_updates,
            'created_time': self.created_time.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GridAttributes':
        """从字典创建实例"""
        # 处理时间字段
        created_time = datetime.fromisoformat(data['created_time']) if 'created_time' in data else datetime.now()
        last_updated = datetime.fromisoformat(data['last_updated']) if 'last_updated' in data else datetime.now()
        
        return cls(
            grid_code=data['grid_code'],
            level=data['level'],
            bbox=data['bbox'],
            center=data['center'],
            alt_range=data['alt_range'],
            flight_rules=data.get('flight_rules', {}),
            airspace_status=data.get('airspace_status', {}),
            weather_conditions=data.get('weather_conditions', {}),
            risk_assessment=data.get('risk_assessment', {}),
            control_authority=data.get('control_authority', {}),
            dynamic_updates=data.get('dynamic_updates', {}),
            created_time=created_time,
            last_updated=last_updated
        )


class GridAttributeManager:
    """网格属性管理器"""
    
    def __init__(self):
        self.grid_attributes: Dict[str, GridAttributes] = {}
    
    def add_grid_attributes(self, attrs: GridAttributes) -> None:
        """添加网格属性"""
        self.grid_attributes[attrs.grid_code] = attrs
    
    def get_grid_attributes(self, grid_code: str) -> Optional[GridAttributes]:
        """获取网格属性"""
        return self.grid_attributes.get(grid_code)
    
    def update_grid_attributes(self, grid_code: str, category: str, key: str, value: Any) -> bool:
        """更新网格属性"""
        if grid_code in self.grid_attributes:
            self.grid_attributes[grid_code].update_attribute(category, key, value)
            return True
        return False
    
    def remove_grid_attributes(self, grid_code: str) -> bool:
        """删除网格属性"""
        if grid_code in self.grid_attributes:
            del self.grid_attributes[grid_code]
            return True
        return False
    
    def get_grids_by_category_value(self, category: str, key: str, value: Any) -> List[GridAttributes]:
        """根据类别和键值查找网格"""
        result = []
        for attrs in self.grid_attributes.values():
            if attrs.get_attribute(category, key) == value:
                result.append(attrs)
        return result
    
    def get_all_grid_codes(self) -> List[str]:
        """获取所有网格编码"""
        return list(self.grid_attributes.keys())
    
    def to_json(self) -> str:
        """导出为JSON格式"""
        data = {code: attrs.to_dict() for code, attrs in self.grid_attributes.items()}
        return json.dumps(data, indent=2)
    
    def from_json(self, json_str: str) -> None:
        """从JSON导入"""
        data = json.loads(json_str)
        self.grid_attributes = {
            code: GridAttributes.from_dict(attrs) for code, attrs in data.items()
        }
