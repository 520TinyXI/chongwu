import random
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

class Pet:
    def __init__(self, name: str, pet_type: str):
        self.name = name
        self.type = pet_type
        self.level = 1
        self.exp = 0
        self.hp = 100
        self.attack = 10
        self.defense = 5
        self.speed = 10
        self.hunger = 50  # 饥饿度 (0-100)
        self.mood = 50    # 心情 (0-100)
        self.skills: List[str] = []
        self.last_updated = datetime.now()
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建Pet实例"""
        pet = cls(data['pet_name'], data['pet_type'])
        pet.level = data.get('level', 1)
        pet.exp = data.get('exp', 0)
        pet.hp = data.get('hp', 100)
        pet.attack = data.get('attack', 10)
        pet.defense = data.get('defense', 5)
        pet.speed = data.get('speed', 10)
        pet.hunger = data.get('hunger', 50)
        pet.mood = data.get('mood', 50)
        pet.skills = data.get('skills', [])
        pet.last_updated = datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat()))
        return pet
        
    def to_dict(self) -> Dict[str, Any]:
        """将Pet实例转换为字典"""
        return {
            'pet_name': self.name,
            'pet_type': self.type,
            'level': self.level,
            'exp': self.exp,
            'hp': self.hp,
            'attack': self.attack,
            'defense': self.defense,
            'speed': self.speed,
            'hunger': self.hunger,
            'mood': self.mood,
            'skills': self.skills,
            'last_updated': self.last_updated.isoformat()
        }
        
    def update_status(self):
        """更新宠物状态（饥饿度和心情随时间下降）"""
        now = datetime.now()
        hours_passed = (now - self.last_updated).total_seconds() / 3600
        
        if hours_passed >= 1:
            hunger_decrease = int(hours_passed * 2)  # 每小时饥饿度下降2点
            mood_decrease = int(hours_passed * 1)    # 每小时心情下降1点
            
            self.hunger = max(0, self.hunger - hunger_decrease)
            self.mood = max(0, self.mood - mood_decrease)
            
            self.last_updated = now
            
    def train(self) -> str:
        """训练宠物"""
        # 检查饥饿度和心情
        if self.hunger <= 10:
            return f"{self.name}太饿了，无法训练！"
        if self.mood <= 10:
            return f"{self.name}心情不好，无法训练！"
            
        # 消耗饥饿度和心情
        self.hunger = max(0, self.hunger - 10)
        self.mood = max(0, self.mood - 5)
        
        # 增加经验值
        exp_gain = random.randint(10, 30)
        self.exp += exp_gain
        
        # 检查是否升级
        level_up = False
        if self.exp >= self.level * 100:
            self.level_up()
            level_up = True
            
        # 更新属性
        self.hp = 80 + self.level * 20
        self.attack = 8 + self.level * 5
        self.defense = 3 + self.level * 3
        self.speed = 8 + self.level * 2
        
        result = f"{self.name}训练成功，获得了{exp_gain}点经验值！"
        if level_up:
            result += f"\n{self.name}升级了！"
            
        return result
        
    def level_up(self):
        """宠物升级"""
        self.level += 1
        self.exp = 0
        
        # 学习新技能（简化实现）
        if self.level % 5 == 0 and len(self.skills) < 4:
            new_skills = ["火球术", "水枪术", "藤鞭", "电击", "治愈术"]
            available_skills = [skill for skill in new_skills if skill not in self.skills]
            if available_skills:
                new_skill = random.choice(available_skills)
                self.skills.append(new_skill)
                
    def is_alive(self) -> bool:
        """检查宠物是否存活"""
        return self.hp > 0
        
    def calculate_damage(self, target) -> int:
        """计算对目标造成的伤害"""
        # 基础伤害 = 攻击力 - 防御力/2
        base_damage = max(1, self.attack - target.defense // 2)
        # 随机波动±20%
        fluctuation = random.uniform(0.8, 1.2)
        damage = int(base_damage * fluctuation)
        return max(1, damage)  # 至少造成1点伤害
        
    def heal(self) -> str:
        """治疗宠物"""
        if self.hp <= 0:
            self.hp = 50  # 复活并恢复一半HP
            self.hunger = max(20, self.hunger)  # 确保有一定饥饿度
            self.mood = max(30, self.mood)      # 确保有一定心情
            return f"{self.name}复活了！HP恢复到{self.hp}点。"
        else:
            # 完全恢复
            hp_restored = 100 + self.level * 20 - self.hp
            self.hp = 100 + self.level * 20
            self.hunger = min(100, self.hunger + 30)
            self.mood = min(100, self.mood + 20)
            return f"{self.name}治疗成功！HP恢复{hp_restored}点，饥饿度和心情也有所改善。"
        
    def __str__(self):
        """返回宠物信息字符串"""
        skills_str = ", ".join(self.skills) if self.skills else "无"
        return f"""宠物信息
名称: {self.name}
类型: {self.type}
等级: {self.level}
经验值: {self.exp}/{self.level * 100}
生命值: {self.hp}
攻击力: {self.attack}
防御力: {self.defense}
速度: {self.speed}
饥饿度: {self.hunger}
心情: {self.mood}
技能: {skills_str}"""