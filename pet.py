import random
import json
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

class Pet:
    # 宠物类型和对应的进化信息
    EVOLUTION_DATA = {
        "烈焰": {"evolve_to": "炽焰龙", "required_level": 10, "type": "火"},
        "碧波兽": {"evolve_to": "瀚海蛟", "required_level": 10, "type": "水"},
        "莲莲草": {"evolve_to": "百草王", "required_level": 10, "type": "草"},
        "碎裂岩": {"evolve_to": "岩脊守护者", "required_level": 10, "type": "土"},
        "金刚": {"evolve_to": "破甲战犀", "required_level": 10, "type": "金"}
    }

    # 属性克制关系
    TYPE_ADVANTAGES = {
        "金": {"木": 1.2, "土": 0.8, "金": 1.0, "水": 1.0, "火": 0.8},
        "木": {"土": 1.2, "水": 0.8, "木": 1.0, "火": 1.0, "金": 0.8},
        "土": {"水": 1.2, "火": 0.8, "土": 1.0, "金": 1.0, "木": 0.8},
        "水": {"火": 1.2, "金": 0.8, "水": 1.0, "木": 1.0, "土": 0.8},
        "火": {"金": 1.2, "木": 0.8, "火": 1.0, "土": 1.0, "水": 0.8}
    }

    # 宠物类型对应的基础图片
    TYPE_IMAGES = {
        "烈焰": "FirePup_1",
        "碧波兽": "WaterSprite_1",
        "莲莲草": "LeafyCat_1",
        "碎裂岩": "cataclastic_rock_1",
        "金刚": "King_Kong_1",
        "炽焰龙": "FirePup_2",
        "瀚海蛟": "WaterSprite_2",
        "百草王": "LeafyCat_2",
        "岩脊守护者": "cataclastic_rock_2",
        "破甲战犀": "King_Kong_2"
    }
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
        self.last_battle_time = datetime.now() - timedelta(hours=1)  # 初始设置为1小时前
        
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
        last_battle_time_str = data.get('last_battle_time')
        if last_battle_time_str:
            pet.last_battle_time = datetime.fromisoformat(last_battle_time_str)
        else:
            pet.last_battle_time = datetime.now() - timedelta(hours=1)
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
            'last_updated': self.last_updated.isoformat(),
            'last_battle_time': self.last_battle_time.isoformat()
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
        while self.exp >= self.level * 100:
            self.exp -= self.level * 100
            self.level += 1

            # 随机提升一项属性
            stat_boost = random.choice(['hp', 'attack', 'defense', 'speed'])
            if stat_boost == 'hp':
                self.hp += 20
            elif stat_boost == 'attack':
                self.attack += 5
            elif stat_boost == 'defense':
                self.defense += 3
            elif stat_boost == 'speed':
                self.speed += 2

            # 升级时学习新技能
            if self.level % 5 == 0:
                new_skill = self.learn_new_skill()
                if new_skill:
                    self.skills.append(new_skill)
                
    def is_alive(self) -> bool:
        """检查宠物是否存活"""
        return self.hp > 0
        
    def calculate_damage(self, opponent) -> int:
        """计算伤害，考虑属性克制"""
        # 基础伤害计算
        damage = max(1, self.attack - opponent.defense // 2)

        # 属性相克
        advantage = self.TYPE_ADVANTAGES.get(self.type, {}).get(opponent.type, 1.0)
        damage = int(damage * advantage)

        # 暴击
        if random.random() < 0.1:
            damage *= 2
            damage = int(damage)

        return damage
        
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
        
    def learn_new_skill(self) -> str:
        """学习新技能"""
        # 根据宠物类型学习不同的技能
        type_skills = {
            '金': ['金刃', '坚固', '反射', '破甲', '金属风暴'],
            '木': ['藤鞭', '光合作用', '种子炸弹', '寄生种子', '森林祝福'],
            '土': ['地震', '岩石封锁', '沙尘暴', '大地守护', '地裂'],
            '水': ['水炮', '冰冻', '水流冲击', '水雾', '海啸'],
            '火': ['火焰冲击', '燃烧', '火球', '火焰之墙', '熔岩爆发']
        }

        # 获取可用技能
        available_skills = type_skills.get(self.type, [])

        # 过滤掉已经学会的技能
        new_skills = [skill for skill in available_skills if skill not in self.skills]

        if new_skills:
            return random.choice(new_skills)
        return ''

    def can_evolve(self) -> bool:
        """检查宠物是否可以进化"""
        return self.name in self.EVOLUTION_DATA and self.level >= self.EVOLUTION_DATA[self.name]['required_level']

    def evolve(self) -> str:
        """宠物进化"""
        if not self.can_evolve():
            return f"{self.name}还不能进化！"

        evolution_info = self.EVOLUTION_DATA[self.name]
        old_name = self.name
        old_type = self.type

        # 更新宠物信息
        self.name = evolution_info['evolve_to']
        self.type = evolution_info['type']

        # 大幅提升属性
        self.hp += 50
        self.attack += 15
        self.defense += 10
        self.speed += 10

        # 学习新技能
        new_skill = self.learn_new_skill()
        if new_skill:
            self.skills.append(new_skill)

        return f"{old_name}进化成了{self.name}！属性大幅提升！"

    def is_battle_available(self) -> bool:
        """检查是否可以进行PVP对战（冷却时间）"""
        now = datetime.now()
        time_since_last_battle = (now - self.last_battle_time).total_seconds() / 60  # 分钟
        return time_since_last_battle >= 30

    def update_battle_time(self):
        """更新最后对战时间"""
        self.last_battle_time = datetime.now()

    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"名称: {self.name}\n"
            f"类型: {self.type}\n"
            f"等级: {self.level}\n"
            f"经验: {self.exp}/{self.level * 100}\n"
            f"属性: HP={self.hp}, 攻击={self.attack}, 防御={self.defense}, 速度={self.speed}\n"
            f"状态: 饥饿度={self.hunger}, 心情={self.mood}\n"
            f"技能: {', '.join(self.skills) if self.skills else '无'}\n"
            f"可进化: {'是' if self.can_evolve() else '否'}"
        )

# PetDatabase类
class PetDatabase:
    def __init__(self, plugin_dir: str):
        db_dir = os.path.join(plugin_dir, "plugins_db")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.db_path = os.path.join(db_dir, "astrbot_plugin_qq_pet.db")
        self.init_db()

    def init_db(self):
        """初始化数据库连接和表结构"""
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # 创建宠物数据表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pet_data (
                user_id TEXT PRIMARY KEY,
                pet_name TEXT,
                pet_type TEXT,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                hp INTEGER DEFAULT 100,
                attack INTEGER DEFAULT 10,
                defense INTEGER DEFAULT 5,
                speed INTEGER DEFAULT 10,
                hunger INTEGER DEFAULT 50,
                mood INTEGER DEFAULT 50,
                skills TEXT DEFAULT '[]',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                last_battle_time TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def create_pet(self, user_id: str, pet_name: str, pet_type: str) -> bool:
        """创建宠物"""
        try:
            # 检查是否已有宠物
            if self.get_pet_data(user_id):
                return False

            self.cursor.execute('''
                INSERT INTO pet_data 
                (user_id, pet_name, pet_type, skills)
                VALUES (?, ?, ?, ?)
            ''', (user_id, pet_name, pet_type, json.dumps([])))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"创建宠物失败: {str(e)}")
            return False

    def get_pet_data(self, user_id: str) -> Dict[str, Any] | None:
        """获取宠物数据"""
        self.cursor.execute('SELECT * FROM pet_data WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return None

        columns = ['user_id', 'pet_name', 'pet_type', 'level', 'exp', 'hp', 'attack', 'defense', 'speed', 'hunger', 'mood', 'skills', 'created_date', 'last_updated', 'last_battle_time']
        data = dict(zip(columns, row))

        # 解析技能列表
        try:
            data['skills'] = json.loads(data['skills'])
        except:
            data['skills'] = []

        return data

    def update_pet_data(self, user_id: str, **kwargs):
        """更新宠物数据"""
        # 更新最后修改时间
        kwargs['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        update_fields = []
        values = []
        for key, value in kwargs.items():
            # 特殊处理技能列表
            if key == 'skills':
                update_fields.append(f"{key} = ?")
                values.append(json.dumps(value))
            else:
                update_fields.append(f"{key} = ?")
                values.append(value)
        values.append(user_id)

        sql = f"UPDATE pet_data SET {', '.join(update_fields)} WHERE user_id = ?"
        self.cursor.execute(sql, values)
        self.conn.commit()

    def delete_pet(self, user_id: str):
        """删除宠物"""
        self.cursor.execute('DELETE FROM pet_data WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def get_all_user_ids(self) -> List[str]:
        """获取所有用户ID"""
        self.cursor.execute('SELECT user_id FROM pet_data')
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]