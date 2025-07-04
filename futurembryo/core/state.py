"""
Cell状态管理模块

定义Cell在执行过程中的各种状态
"""
from enum import Enum
from typing import List


class CellState(Enum):
    """Cell状态枚举 - 定义Cell的生命周期状态"""
    
    IDLE = "idle"                    # 空闲等待
    STARTING = "starting"            # 正在启动
    PROCESSING = "processing"        # 正在处理
    WAITING = "waiting"              # 等待依赖
    COMPLETING = "completing"        # 即将完成
    COMPLETED = "completed"          # 已完成
    ERROR = "error"                  # 出错状态
    PAUSED = "paused"               # 暂停状态
    STOPPED = "stopped"             # 已停止

    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def get_active_states(cls) -> List['CellState']:
        """获取活跃状态列表"""
        return [cls.STARTING, cls.PROCESSING, cls.WAITING, cls.COMPLETING]
    
    @classmethod
    def get_final_states(cls) -> List['CellState']:
        """获取最终状态列表"""
        return [cls.COMPLETED, cls.ERROR, cls.STOPPED]
    
    def is_active(self) -> bool:
        """判断是否为活跃状态"""
        return self in self.get_active_states()
    
    def is_final(self) -> bool:
        """判断是否为最终状态"""
        return self in self.get_final_states() 