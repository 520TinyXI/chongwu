import random
import json
import os
import random
import sqlite3
from typing import Dict, Any, List
from datetime import datetime, timedelta

class Pet:
    # 宠物类型和对应的进化信息
    EVOLUTION_DATA = {
        "烈焰": {"evolve_to": "炽焰龙", "required_level": 10, "type": "火"},
        "碧波兽": {"evolve_to": "瀚海蛟", "required_level": 10, "type": "水"},
        "藤甲虫": {"evolve_to": "赤镰战甲", "required_level": 10, "type": "草"},
        "碎裂岩": {"evolve_to": "岩脊守护者", "required_level": 10, "type": "土"},
        "金刚": {"evolve_to": "破甲战犀", "required_level": 10, "type": "金"}
    }

    # 属性克制关系
    TYPE_ADVANTAGES = {
        "金": {"木": 1.2, "火": 0.8, "金": 1.0, "水": 1.0, "土": 1.0},
        "木": {"土": 1.2, "金": 0.8, "木": 1.0, "火": 1.0, "水": 1.0},
        "土": {"水": 1.2, "木": 0.8, "土": 1.0, "金": 1.0, "火": 1.0},
        "水": {"火": 1.2, "土": 0.8, "水": 1.0, "木": 1.0, "金": 1.0},
        "火": {"金": 1.2, "水": 0.8, "火": 1.0, "土": 1.0, "木": 1.0},
        "暗": {"普通": 1.2, "金": 1.1, "木": 1.0, "火": 1.0, "水": 1.0, "土": 1.0},
        "普通": {"暗": 1.2, "土": 1.1, "金": 1.0, "木": 1.0, "火": 1.0, "水": 1.0}
    }

    # 宠物类型对应的基础图片
    TYPE_IMAGES = {
        "烈焰": "FirePup_1",
        "碧波兽": "WaterSprite_1",
        "藤甲虫": "LeafyCat_1",
        "碎裂岩": "cataclastic_rock_1",
        "金刚": "King_Kong_1",
        "炽焰龙": "FirePup_2",
        "瀚海蛟": "WaterSprite_2",
        "赤镰战甲": "LeafyCat_2",
        "岩脊守护者": "cataclastic_rock_2",
        "破甲战犀": "King_Kong_2"
    }
    def __init__(self, name: str, pet_type: str, owner: str = "未知"):
        self.name = name
        self.type = pet_type
        self.owner = owner
        self.level = 1
        self.exp = 0
        
        # 根据宠物类型设置基础属性
        base_stats = {
            "火": {"hp": 40, "attack": 16, "defense": 5, "speed": 13},
            "水": {"hp": 50, "attack": 10, "defense": 8, "speed": 10},
            "草": {"hp": 60, "attack": 8, "defense": 12, "speed": 8},
            "土": {"hp": 70, "attack": 7, "defense": 10, "speed": 6},
            "金": {"hp": 45, "attack": 14, "defense": 6, "speed": 14},
            "暗": {"hp": 55, "attack": 12, "defense": 7, "speed": 11},
            "普通": {"hp": 50, "attack": 10, "defense": 6, "speed": 9}
        }
        
        stats = base_stats.get(pet_type, {"hp": 40, "attack": 10, "defense": 5, "speed": 10})
        self.hp = stats["hp"]
        self.attack = stats["attack"]
        self.defense = stats["defense"]
        self.speed = stats["speed"]
        
        self.hunger = 50  # 饥饿度 (0-100)
        self.mood = 50    # 心情 (0-100)
        self.coins = 0    # 金币
        self.skills: List[str] = []
        self.skill_unlocked = False  # 是否已解锁技能
        self.burn_turns = 0  # 灼烧效果剩余回合数
        self.heal_blocked_turns = 0  # 禁疗效果剩余回合数
        self.defense_boost = 0  # 防御加成
        self.crit_rate_boost = 0  # 暴击率加成
        self.revive_used = False  # 复活技能是否已使用
        self.last_updated = datetime.now()
        self.last_battle_time = datetime.now() - timedelta(hours=1)  # 初始设置为1小时前
        self.auto_heal_threshold = 100  # 自动使用治疗瓶的最低血量阈值
        
        # 暴击属性
        self.critical_rate = 0.05  # 基础暴击率
        self.critical_damage = 1.5  # 基础暴击伤害
        
        # 金属性专属暴击属性
        if self.type == "金":
            if self.name == "金刚":
                self.critical_rate = 0.15  # 15%暴击率
                self.critical_damage = 1.8  # 180%暴击伤害
            elif self.name == "破甲战犀":
                self.critical_rate = 0.25  # 25%暴击率
                self.critical_damage = 1.8  # 180%暴击伤害
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建Pet实例"""
        pet = cls(data['pet_name'], data['pet_type'], data.get('owner', '未知'))
        pet.level = data.get('level', 1)
        pet.exp = data.get('exp', 0)
        pet.hp = data.get('hp', 100)
        pet.attack = data.get('attack', 10)
        pet.defense = data.get('defense', 5)
        pet.speed = data.get('speed', 10)
        pet.hunger = data.get('hunger', 50)
        pet.mood = data.get('mood', 50)
        pet.coins = data.get('coins', 0)
        # 解析技能列表
        try:
            pet.skills = json.loads(data.get('skills', '[]'))
        except:
            pet.skills = []
        pet.last_updated = datetime.fromisoformat(data.get('last_updated', datetime.now().isoformat()))
        last_battle_time_str = data.get('last_battle_time')
        if last_battle_time_str:
            pet.last_battle_time = datetime.fromisoformat(last_battle_time_str)
        else:
            pet.last_battle_time = datetime.now() - timedelta(hours=1)
        pet.auto_heal_threshold = data.get('auto_heal_threshold', 100)
        pet.critical_rate = data.get('critical_rate', 0.05)
        pet.critical_damage = data.get('critical_damage', 1.5)
        pet.skill_unlocked = data.get('skill_unlocked', False)
        pet.burn_turns = data.get('burn_turns', 0)
        pet.heal_blocked_turns = data.get('heal_blocked_turns', 0)
        pet.defense_boost = data.get('defense_boost', 0)
        pet.crit_rate_boost = data.get('crit_rate_boost', 0)
        pet.revive_used = data.get('revive_used', False)
        return pet
        
    def to_dict(self) -> Dict[str, Any]:
        """将Pet实例转换为字典"""
        return {
            'pet_name': self.name,
            'pet_type': self.type,
            'owner': self.owner,
            'level': self.level,
            'exp': self.exp,
            'hp': self.hp,
            'attack': self.attack,
            'defense': self.defense,
            'speed': self.speed,
            'hunger': self.hunger,
            'mood': self.mood,
            'coins': self.coins,
            'skills': json.dumps(self.skills),
            'last_updated': self.last_updated.isoformat(),
            'last_battle_time': self.last_battle_time.isoformat(),
            'auto_heal_threshold': self.auto_heal_threshold,
            'critical_rate': self.critical_rate,
            'critical_damage': self.critical_damage,
            'skill_unlocked': self.skill_unlocked,
            'burn_turns': self.burn_turns,
            'heal_blocked_turns': self.heal_blocked_turns,
            'defense_boost': self.defense_boost,
            'crit_rate_boost': self.crit_rate_boost,
            'revive_used': self.revive_used
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
            
    def update_stats(self):
        """更新宠物属性"""
        # 根据宠物类型和等级计算属性
        type_growth = {
            "火": {"hp": 15, "attack": 3.8, "defense": 1.5, "speed": 3.0},
            "水": {"hp": 16, "attack": 3.0, "defense": 2.0, "speed": 2.5},
            "草": {"hp": 18, "attack": 2.5, "defense": 3.0, "speed": 2.0},
            "土": {"hp": 20, "attack": 2.2, "defense": 2.5, "speed": 1.8},
            "金": {"hp": 16, "attack": 3.5, "defense": 1.8, "speed": 3.2},
            "暗": {"hp": 17, "attack": 3.2, "defense": 2.0, "speed": 2.8},
            "普通": {"hp": 16, "attack": 3.0, "defense": 1.8, "speed": 2.4}
        }
        
        # 进化形态属性
        evolved_growth = {
            "火": {"hp": 19, "attack": 4.8, "defense": 1.9, "speed": 3.8},
            "水": {"hp": 20, "attack": 3.8, "defense": 2.5, "speed": 3.1},
            "草": {"hp": 23, "attack": 3.1, "defense": 3.8, "speed": 2.5},
            "土": {"hp": 25, "attack": 2.8, "defense": 3.1, "speed": 2.3},
            "金": {"hp": 20, "attack": 4.4, "defense": 2.3, "speed": 4.0},
            "暗": {"hp": 22, "attack": 4.2, "defense": 2.5, "speed": 3.5},
            "普通": {"hp": 21, "attack": 4.0, "defense": 2.3, "speed": 3.1}
        }
        
        # 基础形态基础属性
        base_stats = {
            "火": {"hp": 40, "attack": 16, "defense": 5, "speed": 13},
            "水": {"hp": 50, "attack": 10, "defense": 8, "speed": 10},
            "草": {"hp": 60, "attack": 8, "defense": 12, "speed": 8},
            "土": {"hp": 70, "attack": 7, "defense": 10, "speed": 6},
            "金": {"hp": 45, "attack": 14, "defense": 6, "speed": 14},
            "暗": {"hp": 55, "attack": 12, "defense": 7, "speed": 11},
            "普通": {"hp": 50, "attack": 10, "defense": 6, "speed": 9}
        }
        
        # 进化形态基础属性（30级）
        evolved_base = {
            "火": {"hp": 600, "attack": 158, "defense": 61, "speed": 125},
            "水": {"hp": 643, "attack": 121, "defense": 83, "speed": 103},
            "草": {"hp": 728, "attack": 101, "defense": 124, "speed": 83},
            "土": {"hp": 813, "attack": 89, "defense": 103, "speed": 73},
            "金": {"hp": 636, "attack": 144, "defense": 73, "speed": 134},
            "暗": {"hp": 620, "attack": 135, "defense": 75, "speed": 110},
            "普通": {"hp": 630, "attack": 130, "defense": 70, "speed": 105}
        }
        
        # 判断是否为进化形态
        is_evolved = self.level >= 30 and self.name in ["炽焰龙", "瀚海蛟", "赤镰战甲", "岩脊守护者", "破甲战犀"]
        
        if is_evolved:
            # 进化形态属性计算
            growth = evolved_growth.get(self.type, evolved_growth["火"])
            base = evolved_base.get(self.type, evolved_base["火"])
            # 30级基础属性 + (当前等级-30) * 每级成长
            level_diff = self.level - 30
            self.hp = int(base["hp"] + level_diff * growth["hp"])
            self.attack = int(base["attack"] + level_diff * growth["attack"])
            self.defense = int(base["defense"] + level_diff * growth["defense"])
            self.speed = int(base["speed"] + level_diff * growth["speed"])
        else:
            # 基础形态属性计算
            growth = type_growth.get(self.type, type_growth["火"])
            base = base_stats.get(self.type, base_stats["火"])
            # 基础属性 + (当前等级-1) * 每级成长
            level_diff = self.level - 1
            self.hp = int(base["hp"] + level_diff * growth["hp"])
            self.attack = int(base["attack"] + level_diff * growth["attack"])
            self.defense = int(base["defense"] + level_diff * growth["defense"])
            self.speed = int(base["speed"] + level_diff * growth["speed"])
        
        # 金属性宠物暴击属性成长
        if self.type == "金":
            if self.name == "金刚":
                # 每级暴击率+0.2%、暴伤+0.3%
                level_diff = self.level - 1
                self.critical_rate = 0.15 + level_diff * 0.002
                self.critical_damage = 1.8 + level_diff * 0.003
            elif self.name == "破甲战犀":
                # 每级暴击率+0.3%、暴伤+0.4%
                level_diff = self.level - 1
                self.critical_rate = 0.25 + level_diff * 0.003
                self.critical_damage = 1.8 + level_diff * 0.004
            else:
                # 其他金属性宠物使用基础暴击属性
                self.critical_rate = 0.05
                self.critical_damage = 1.5
        else:
            # 非金属性宠物使用基础暴击属性
            self.critical_rate = 0.05
            self.critical_damage = 1.5
        
        # 10级解锁技能
        if self.level >= 10 and not self.skill_unlocked:
            self.skill_unlocked = True
            # 根据宠物名称设置对应的技能
            if self.name == "烈焰":
                self.skills = ["火焰焚烧"]
            elif self.name == "碧波兽":
                self.skills = ["巨浪淹没"]
            elif self.name == "藤甲虫":
                self.skills = ["根须缠绕"]
            elif self.name == "碎裂岩":
                self.skills = ["大地堡垒"]
            elif self.name == "金刚":
                self.skills = ["金属风暴"]
            # 进化形态也继承技能
            elif self.name == "炽焰龙":
                self.skills = ["火焰焚烧"]
            elif self.name == "瀚海蛟":
                self.skills = ["巨浪淹没"]
            elif self.name == "赤镰战甲":
                self.skills = ["根须缠绕"]
            elif self.name == "岩脊守护者":
                self.skills = ["大地堡垒"]
            elif self.name == "破甲战犀":
                self.skills = ["金属风暴"]
                
    def is_alive(self) -> bool:
        """检查宠物是否存活"""
        return self.hp > 0
        
    def calculate_damage(self, opponent, skill_multiplier: float = 1.0) -> dict:
        """计算伤害，考虑属性克制、技能系数、暴击等"""
        # 基础伤害计算：伤害 = (攻击力 × 技能系数 - 防御力 × 0.3) × 克制系数
        base_damage = self.attack * skill_multiplier - opponent.defense * 0.3
        damage = max(1, base_damage)

        # 属性相克
        advantage = self.TYPE_ADVANTAGES.get(self.type, {}).get(opponent.type, 1.0)
        damage = damage * advantage

        # 暴击判定
        is_critical = random.random() < self.critical_rate
        critical_damage = 0
        
        # 暴击效果
        if is_critical:
            # 计算暴击伤害
            critical_damage = damage * self.critical_damage
            
            # 金属性专属特效
            if self.type == "金":
                if self.name == "金刚":
                    # 暴击时无视20%防御
                    damage = self.attack * skill_multiplier - opponent.defense * 0.3 * 0.8
                    damage = max(1, damage)
                    damage = damage * advantage
                    critical_damage = damage * self.critical_damage
                elif self.name == "破甲战犀":
                    # 暴击时额外造成攻击力30%的真实伤害
                    additional_damage = self.attack * 0.3
                    critical_damage += additional_damage
            
            # 其他属性暴击联动效果
            elif self.type == "火":
                # 暴击时附加"灼烧"效果（3回合5%最大生命伤害）
                pass  # 灼烧效果需要在战斗循环中实现
            elif self.type == "水":
                # 暴击时回复15%造成伤害的生命值
                heal_amount = int(critical_damage * 0.15)
                self.hp = min(self.hp + heal_amount, self.hp)  # 需要获取最大HP
            elif self.type == "草":
                # 暴击时获得10%最大生命的护盾
                pass  # 护盾效果需要额外实现
            elif self.type == "土":
                # 暴击时降低目标20%防御（2回合）
                pass  # 防御降低效果需要在战斗循环中实现
            
            # 限制暴击伤害上限为3倍基础伤害
            critical_damage = min(critical_damage, damage * 3)
            
            return {
                "damage": int(critical_damage),
                "is_critical": True,
                "critical_rate": self.critical_rate,
                "critical_damage": self.critical_damage
            }
        else:
            return {
                "damage": int(damage),
                "is_critical": False,
                "critical_rate": self.critical_rate,
                "critical_damage": self.critical_damage
            }
        
    def heal(self) -> str:
        """治疗宠物"""
        if self.hp <= 0:
            self.hp = 50  # 复活并恢复一半HP
            self.hunger = max(20, self.hunger)  # 确保有一定饥饿度
            self.mood = max(30, self.mood)      # 确保有一定心情
            return f"{self.name}复活了！HP恢复到{self.hp}点。"
        else:
            # 完全恢复
            old_hp = self.hp
            self.update_stats()  # 更新属性以获取当前等级的最大HP
            hp_restored = self.hp - old_hp
            self.hunger = min(100, self.hunger + 30)
            self.mood = min(100, self.mood + 20)
            return f"{self.name}治疗成功！HP恢复{hp_restored}点，饥饿度和心情也有所改善。"
        
    def learn_new_skill(self) -> str:
        """学习新技能"""
        # 根据宠物类型学习不同的技能
        type_skills = {
            '金': ['金属风暴'],
            '木': ['根须缠绕'],
            '土': ['大地堡垒'],
            '水': ['巨浪淹没'],
            '火': ['火焰焚烧']
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

        # 重置属性为进化形态的1级属性
        evolved_base = {
            "火": {"hp": 600, "attack": 158, "defense": 61, "speed": 125},
            "水": {"hp": 643, "attack": 121, "defense": 83, "speed": 103},
            "草": {"hp": 728, "attack": 101, "defense": 124, "speed": 83},
            "土": {"hp": 813, "attack": 89, "defense": 103, "speed": 73},
            "金": {"hp": 636, "attack": 144, "defense": 73, "speed": 134}
        }
        
        base = evolved_base.get(self.type, evolved_base["火"])
        self.hp = base["hp"]
        self.attack = base["attack"]
        self.defense = base["defense"]
        self.speed = base["speed"]

        # 学习新技能
        new_skill = self.learn_new_skill()
        if new_skill:
            self.skills.append(new_skill)

        return f"{old_name}进化成了{self.name}！属性重置为：\nHP{self.hp} 攻击{self.attack} 防御{self.defense} 速度{self.speed}"

    def is_battle_available(self) -> bool:
        """检查是否可以进行PVP对战（冷却时间）"""
        now = datetime.now()
        time_since_last_battle = (now - self.last_battle_time).total_seconds() / 60  # 分钟
        return time_since_last_battle >= 30

    def update_battle_time(self):
        """更新最后对战时间"""
        self.last_battle_time = datetime.now()

    def level_up(self):
        """升级处理"""
        self.level += 1
        self.exp = 0  # 重置经验值
        self.update_stats()  # 更新属性
        
        # 学习新技能
        new_skill = self.learn_new_skill()
        if new_skill:
            self.skills.append(new_skill)
        
        # 进化检查
        if self.can_evolve():
            return self.evolve()
        
        return f"{self.name}升级到{self.level}级！"

    def __str__(self) -> str:
        """返回宠物的详细信息"""
        # 计算战力值（简化计算）
        power = self.attack + self.defense + self.speed
        
        # 格式化技能列表
        skills_str = "、".join(self.skills) if self.skills else "无"
        
        # 获取宠物的原始名称
        original_name = self.name
        
        return f"""主人：{self.owner}
名称：{self.name} {original_name}
属性：{self.type}
战力值：{power}
等级：{self.level}
经验值：{self.exp}/{self.level * 100}
生命值：{self.hp}
攻击力：{self.attack}
防御力：{self.defense}
速度：{self.speed}
暴击率：{self.critical_rate:.1%}
暴击伤害：{self.critical_damage:.0%}
技能：{skills_str}"""

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
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # 创建宠物数据表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pet_data (
                user_id TEXT PRIMARY KEY,
                pet_name TEXT,
                pet_type TEXT,
                owner TEXT DEFAULT '未知',
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                hp INTEGER DEFAULT 100,
                attack INTEGER DEFAULT 10,
                defense INTEGER DEFAULT 5,
                speed INTEGER DEFAULT 10,
                hunger INTEGER DEFAULT 50,
                mood INTEGER DEFAULT 50,
                coins INTEGER DEFAULT 0,
                skills TEXT DEFAULT '[]',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                last_battle_time TEXT DEFAULT CURRENT_TIMESTAMP,
                auto_heal_threshold INTEGER DEFAULT 100,
                critical_rate REAL DEFAULT 0.05,
                critical_damage REAL DEFAULT 1.5
            )
        ''')
        
        # 为已存在的记录添加默认的暴击属性值
        try:
            self.cursor.execute('ALTER TABLE pet_data ADD COLUMN critical_rate REAL DEFAULT 0.05')
            print("已添加critical_rate字段")
        except sqlite3.OperationalError as e:
            # 列已存在，忽略错误
            print(f"critical_rate字段已存在: {e}")
            pass
            
        try:
            self.cursor.execute('ALTER TABLE pet_data ADD COLUMN critical_damage REAL DEFAULT 1.5')
            print("已添加critical_damage字段")
        except sqlite3.OperationalError as e:
            # 列已存在，忽略错误
            print(f"critical_damage字段已存在: {e}")
            pass

        # 添加技能解锁字段
        try:
            self.cursor.execute('ALTER TABLE pet_data ADD COLUMN skill_unlocked TEXT DEFAULT ""')
            print("已添加skill_unlocked字段")
        except sqlite3.OperationalError as e:
            # 列已存在，忽略错误
            print(f"skill_unlocked字段已存在: {e}")
            pass

        # 创建商店物品表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price INTEGER NOT NULL,
                effect_type TEXT NOT NULL,
                effect_value INTEGER NOT NULL,
                effect_value2 INTEGER DEFAULT 0
            )
        ''')

        # 创建用户背包表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                user_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, item_name)
            )
        ''')

        self.conn.commit()

        # 初始化商店物品
        self._init_shop_items()

    def _init_shop_items(self):
        """初始化商店物品"""
        # 检查是否已有物品
        self.cursor.execute('SELECT COUNT(*) FROM shop_items')
        count = self.cursor.fetchone()[0]
        
        if count == 0:
            # 插入商店物品
            items = [
                ("普通口粮", "能快速填饱肚子的基础食物。", 20, "hunger", 20, 0),
                ("美味罐头", "营养均衡，宠物非常爱吃。", 50, "hunger_mood", 20, 20),
                ("开心饼干", "能让宠物心情愉悦的神奇零食。", 35, "mood", 20, 0),
                ("小治疗瓶", "能恢复宠物20血量", 20, "hp", 20, 0),
                ("中治疗瓶", "能恢复宠物50血量", 100, "hp", 50, 0),
                ("大治疗瓶", "能恢复宠物100血量", 200, "hp", 100, 0)
            ]
            
            self.cursor.executemany('''
                INSERT INTO shop_items (name, description, price, effect_type, effect_value, effect_value2)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', items)
            
            self.conn.commit()

    def get_shop_items(self) -> List[Dict[str, Any]]:
        """获取商店物品列表"""
        self.cursor.execute('SELECT * FROM shop_items')
        rows = self.cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'effect_type': row[4],
                'effect_value': row[5],
                'effect_value2': row[6]
            })
        
        return items

    def get_user_inventory(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户背包物品"""
        self.cursor.execute('SELECT item_name, quantity FROM user_inventory WHERE user_id = ?', (user_id,))
        rows = self.cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                'name': row[0],
                'quantity': row[1]
            })
        
        return items

    def add_item_to_inventory(self, user_id: str, item_name: str, quantity: int = 1):
        """添加物品到用户背包"""
        # 检查是否已存在该物品
        self.cursor.execute('''
            SELECT quantity FROM user_inventory 
            WHERE user_id = ? AND item_name = ?
        ''', (user_id, item_name))
        
        row = self.cursor.fetchone()
        if row:
            # 更新数量
            new_quantity = row[0] + quantity
            self.cursor.execute('''
                UPDATE user_inventory 
                SET quantity = ? 
                WHERE user_id = ? AND item_name = ?
            ''', (new_quantity, user_id, item_name))
        else:
            # 插入新记录
            self.cursor.execute('''
                INSERT INTO user_inventory (user_id, item_name, quantity)
                VALUES (?, ?, ?)
            ''', (user_id, item_name, quantity))
        
        self.conn.commit()

    def remove_item_from_inventory(self, user_id: str, item_name: str, quantity: int = 1) -> bool:
        """从用户背包移除物品"""
        # 检查是否拥有足够数量的物品
        self.cursor.execute('''
            SELECT quantity FROM user_inventory 
            WHERE user_id = ? AND item_name = ?
        ''', (user_id, item_name))
        
        row = self.cursor.fetchone()
        if not row:
            return False
        
        current_quantity = row[0]
        if current_quantity < quantity:
            return False
        
        # 更新数量
        new_quantity = current_quantity - quantity
        if new_quantity <= 0:
            # 删除记录
            self.cursor.execute('''
                DELETE FROM user_inventory 
                WHERE user_id = ? AND item_name = ?
            ''', (user_id, item_name))
        else:
            # 更新数量
            self.cursor.execute('''
                UPDATE user_inventory 
                SET quantity = ? 
                WHERE user_id = ? AND item_name = ?
            ''', (new_quantity, user_id, item_name))
        
        self.conn.commit()
        return True

    def use_item_on_pet(self, user_id: str, item_name: str, pet: Pet) -> str:
        """对宠物使用物品"""
        # 检查是否拥有该物品
        self.cursor.execute('''
            SELECT quantity FROM user_inventory 
            WHERE user_id = ? AND item_name = ?
        ''', (user_id, item_name))
        
        row = self.cursor.fetchone()
        if not row or row[0] <= 0:
            return f"你没有{item_name}！"
        
        # 获取物品效果
        self.cursor.execute('''
            SELECT effect_type, effect_value, effect_value2 FROM shop_items 
            WHERE name = ?
        ''', (item_name,))
        
        item_row = self.cursor.fetchone()
        if not item_row:
            return f"无效的物品{item_name}！"
        
        effect_type, effect_value, effect_value2 = item_row
        
        # 应用效果
        result = f"使用了{item_name}！"
        if effect_type == "hunger":
            pet.hunger = min(100, pet.hunger + effect_value)
            result += f"\n{pet.name}的饥饿度恢复了{effect_value}点！"
        elif effect_type == "mood":
            pet.mood = min(100, pet.mood + effect_value)
            result += f"\n{pet.name}的心情恢复了{effect_value}点！"
        elif effect_type == "hp":
            hp_restored = min(effect_value, (100 + pet.level * 20) - pet.hp)
            pet.hp = min(100 + pet.level * 20, pet.hp + effect_value)
            result += f"\n{pet.name}的HP恢复了{hp_restored}点！"
        elif effect_type == "hunger_mood":
            pet.hunger = min(100, pet.hunger + effect_value)
            pet.mood = min(100, pet.mood + effect_value2)
            result += f"\n{pet.name}的饥饿度恢复了{effect_value}点，心情恢复了{effect_value2}点！"
        
        # 从背包中移除物品
        self.remove_item_from_inventory(user_id, item_name, 1)
        
        return result

    def create_pet(self, user_id: str, pet_name: str, pet_type: str, owner: str = "未知") -> bool:
        """创建宠物"""
        try:
            # 检查是否已有宠物
            if self.get_pet_data(user_id):
                return False

            self.cursor.execute('''
                INSERT INTO pet_data 
                (user_id, pet_name, pet_type, skills, owner)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, pet_name, pet_type, json.dumps([]), owner))

            self.conn.commit()
            return True
        except Exception as e:
            print(f"创建宠物失败: {str(e)}")
            return False

    def get_pet_data(self, user_id: str) -> Dict[str, Any] | None:
        """获取宠物数据"""
        self.cursor.execute('''
            SELECT user_id, pet_name, pet_type, owner, level, exp, hp, attack, defense, speed, 
                   hunger, mood, coins, skills, last_updated, last_battle_time, auto_heal_threshold,
                   critical_rate, critical_damage, skill_unlocked
            FROM pet_data 
            WHERE user_id = ?
        ''', (user_id,))
        
        row = self.cursor.fetchone()
        if not row:
            return None

        columns = ['user_id', 'pet_name', 'pet_type', 'owner', 'level', 'exp', 'hp', 'attack', 'defense', 'speed', 
                  'hunger', 'mood', 'coins', 'skills', 'last_updated', 'last_battle_time', 'auto_heal_threshold',
                  'critical_rate', 'critical_damage', 'skill_unlocked']
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
        
        # 构建SET子句
        set_clause = ', '.join([f"{key}=?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        
        query = f"UPDATE pet_data SET {set_clause} WHERE user_id=?"
        self.cursor.execute(query, values)
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