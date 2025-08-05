# -*- coding: utf-8 -*-
import os
import random
import logging
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
import sys
import json
import sqlite3
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# PetDatabase类
class PetDatabase:
    def __init__(self, plugin_dir: str):
        db_dir = os.path.join(plugin_dir, "plugins_db")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.db_path = os.path.join(db_dir, "astrbot_plugin_qq_pet.db")
        self.init_db()  # 确保调用初始化方法
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
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
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
    
    def get_pet_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取宠物数据"""
        self.cursor.execute('SELECT * FROM pet_data WHERE user_id = ?', (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        
        columns = ['user_id', 'pet_name', 'pet_type', 'level', 'exp', 'hp', 'attack', 'defense', 'speed', 'hunger', 'mood', 'skills', 'created_date', 'last_updated']
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
        
    def save_pet_data(self, user_id: str, pet_data: Dict[str, Any]):
        """保存宠物数据（用于创建宠物）"""
        try:
            self.conn.execute("BEGIN")
            # 检查是否已有宠物
            if self.get_pet_data(user_id):
                self.conn.rollback()
                return False
            
            self.cursor.execute('''
                INSERT INTO pet_data 
                (user_id, pet_name, pet_type, level, exp, hp, attack, defense, speed, hunger, mood, skills)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                pet_data['pet_name'],
                pet_data['pet_type'],
                pet_data.get('level', 1),
                pet_data.get('exp', 0),
                pet_data.get('hp', 100),
                pet_data.get('attack', 10),
                pet_data.get('defense', 5),
                pet_data.get('speed', 10),
                pet_data.get('hunger', 50),
                pet_data.get('mood', 50),
                json.dumps(pet_data.get('skills', []))
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"保存宠物数据失败: {str(e)}")
            return False

# PetImageGenerator类
class PetImageGenerator:
    def __init__(self, plugin_dir: str):
        self.bg_image = os.path.join(plugin_dir, "assets", "Basemap.png")
        self.font_path = os.path.join(plugin_dir, "assets", "font.ttf")

    async def create_pet_image(self, text: str, font_size: int = 36) -> Union[str, None]:
        """生成宠物信息图片"""
        try:
            if not os.path.exists(self.bg_image):
                return None

            bg = Image.open(self.bg_image)
            if bg.size != (1640, 856):
                bg = bg.resize((1640, 856))

            draw = ImageDraw.Draw(bg)

            try:
                if os.path.exists(self.font_path):
                    font = ImageFont.truetype(self.font_path, font_size)
                else:
                    font = ImageFont.load_default()
                    font_size = 16
            except Exception:
                font = ImageFont.load_default()
                font_size = 16

            # 处理多行文本
            lines = text.split('\n')
            y_offset = 100
            line_spacing = font_size + 10
            
            for line in lines:
                # 计算文本位置（居中）
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (1640 - text_width) / 2
                y = y_offset
                
                draw.text((x, y), line, font=font, fill=(0, 0, 0))
                y_offset += line_spacing

            temp_path = os.path.join(os.path.dirname(self.bg_image), "temp_pet.png")
            bg.save(temp_path)
            return temp_path
        except Exception as e:
            print(f"生成图片失败: {e}")
            return None

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
        
    def learn_new_skill(self) -> str:
        """学习新技能"""
        # 根据宠物类型学习不同的技能
        type_skills = {
            '火': ['火焰冲击', '燃烧', '火球', '火焰之墙', '熔岩爆发'],
            '水': ['水炮', '冰冻', '水流冲击', '水雾', '海啸'],
            '草': ['藤鞭', '光合作用', '种子炸弹', '寄生种子', '森林祝福'],
            '电': ['电击', '雷鸣', '电磁脉冲', '电网', '十万伏特'],
            '普通': ['撞击', '叫声', '瞪眼', '摇尾巴', '突进']
        }
        
        # 获取可用技能
        available_skills = type_skills.get(self.type, type_skills['普通'])
        
        # 过滤掉已经学会的技能
        new_skills = [skill for skill in available_skills if skill not in self.skills]
        
        if new_skills:
            return random.choice(new_skills)
        return ''
        
    def calculate_damage(self, opponent) -> int:
        """计算伤害"""
        # 基础伤害计算
        damage = max(1, self.attack - opponent.defense // 2)
        
        # 属性相克
        type_advantages = {
            '火': {'草': 2, '水': 0.5, '火': 1, '电': 1, '普通': 1},
            '水': {'火': 2, '草': 0.5, '水': 1, '电': 0.5, '普通': 1},
            '草': {'水': 2, '火': 0.5, '草': 1, '电': 1, '普通': 1},
            '电': {'水': 2, '火': 1, '草': 1, '电': 1, '普通': 1},
            '普通': {'火': 1, '水': 1, '草': 1, '电': 1, '普通': 1}
        }
        
        advantage = type_advantages.get(self.type, {}).get(opponent.type, 1)
        damage = int(damage * advantage)
        
        # 暴击
        if random.random() < 0.1:
            damage *= 2
            damage = int(damage)
        
        return damage
        
    def is_alive(self) -> bool:
        """检查宠物是否存活"""
        return self.hp > 0
        
    def __str__(self) -> str:
        """字符串表示"""
        return (
            f"名称: {self.name}\n"\
            f"类型: {self.type}\n"\
            f"等级: {self.level}\n"\
            f"经验: {self.exp}/{self.level * 100}\n"\
            f"属性: HP={self.hp}, 攻击={self.attack}, 防御={self.defense}, 速度={self.speed}\n"\
            f"状态: 饥饿度={self.hunger}, 心情={self.mood}\n"\
            f"技能: {', '.join(self.skills) if self.skills else '无'}"
        )

logger = logging.getLogger(__name__)


@register("宠物", "Tinyxi", "一个QQ宠物插件，包含创建宠物、喂养、训练、对战等功能", "1.0.0", "https://github.com/520TinyXI/chongwu.git")
class QQPetPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        plugin_dir = os.path.dirname(__file__)
        
        # 确保资源目录存在
        assets_dir = os.path.join(plugin_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            logger.warning(f"创建资源目录: {assets_dir}")
        
        self.db = PetDatabase(plugin_dir)
        self.img_gen = PetImageGenerator(plugin_dir)
        self.pets: Dict[str, Pet] = {}
        
        # 初始化已有的宠物
        self._load_existing_pets()
    
    async def terminate(self):
        '''插件终止时调用'''
        pass
    
    def _load_existing_pets(self):
        """加载已有的宠物数据"""
        # 获取所有用户ID
        user_ids = self.db.get_all_user_ids()
        for user_id in user_ids:
            pet_data = self.db.get_pet_data(user_id)
            if pet_data:
                self.pets[user_id] = Pet.from_dict(pet_data)
    
    @filter.command("创建宠物")
    async def create_pet(self, event: AstrMessageEvent):
        """创建宠物"""
        try:
            user_id = event.get_sender_id()
            logger.info(f"用户 {user_id} 请求创建宠物")
            
            # 双重检查是否已创建宠物
            if user_id in self.pets or self.db.get_pet_data(user_id):
                yield event.plain_result("您已经创建了宠物！")
                return
            
            # 获取宠物名称（如果提供了的话）
            args = event.get_args()
            pet_name = args[0] if args else f"宠物{user_id[-4:]}"  # 默认名称
            
            # 随机选择宠物类型
            pet_types = ["火", "水", "草", "电", "普通"]
            pet_type = random.choice(pet_types)
            
            # 创建宠物
            pet = Pet(pet_name, pet_type)
            self.pets[user_id] = pet
            
            # 保存到数据库
            self.db.save_pet_data(user_id, pet.to_dict())
            
            # 生成结果图片
            result = f"成功创建宠物！\n名称: {pet.name}\n类型: {pet.type}\n属性: HP={pet.hp}, 攻击={pet.attack}, 防御={pet.defense}, 速度={pet.speed}"
            image_path = await self.img_gen.create_pet_image(result)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"创建宠物失败: {str(e)}")
            yield event.plain_result("创建宠物失败了~请联系管理员检查日志")
    
    @filter.command("查看宠物")
    async def view_pet(self, event: AstrMessageEvent):
        """查看宠物信息"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'创建宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 更新宠物状态
            pet.update_status()
            
            # 保存到数据库
            self.db.update_pet_data(user_id, **pet.to_dict())
            
            # 生成结果图片
            result = str(pet)
            image_path = await self.img_gen.create_pet_image(result)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"查看宠物失败: {str(e)}")
            yield event.plain_result("查看宠物失败了~请联系管理员检查日志")
    
    @filter.command("训练宠物")
    async def train_pet(self, event: AstrMessageEvent):
        """训练宠物"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'创建宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 训练宠物
            result = pet.train()
            
            # 更新数据库
            self.db.update_pet_data(
                user_id,
                level=pet.level,
                exp=pet.exp,
                hp=pet.hp,
                attack=pet.attack,
                defense=pet.defense,
                speed=pet.speed,
                hunger=pet.hunger,
                mood=pet.mood,
                skills=pet.skills
            )
            
            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"训练宠物失败: {str(e)}")
            yield event.plain_result("训练宠物失败了~请联系管理员检查日志")
    
    @filter.command("宠物对战")
    async def battle_pet(self, event: AstrMessageEvent):
        """宠物对战"""

        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'创建宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 检查宠物是否存活
            if not pet.is_alive():
                yield event.plain_result(f"{pet.name}已经失去战斗能力，请先治疗！")
                return
            
            # 创建对手宠物（随机生成）
            opponent_types = ["火", "水", "草", "电", "普通"]
            opponent_type = random.choice(opponent_types)
            opponent = Pet(f"野生{opponent_type}宠物", opponent_type)
            
            # 设置对手等级为当前宠物等级±2级
            level_diff = random.randint(-2, 2)
            opponent.level = max(1, pet.level + level_diff)
            
            # 根据等级调整对手属性
            opponent.hp = 80 + opponent.level * 20
            opponent.attack = 8 + opponent.level * 5
            opponent.defense = 3 + opponent.level * 3
            opponent.speed = 8 + opponent.level * 2
            
            # 对战过程
            battle_log = f"{pet.name} vs {opponent.name}\n" + "="*30 + "\n"
            
            # 决定先手
            player_first = pet.speed >= opponent.speed
            
            while pet.is_alive() and opponent.is_alive():
                if player_first:
                    # 玩家攻击
                    damage = pet.calculate_damage(opponent)
                    opponent.hp = max(0, opponent.hp - damage)
                    battle_log += f"{pet.name}攻击{opponent.name}，造成{damage}点伤害！\n"
                    
                    # 检查对手是否被击败
                    if not opponent.is_alive():
                        battle_log += f"{opponent.name}被击败了！\n"
                        break
                    
                    # 对手攻击
                    damage = opponent.calculate_damage(pet)
                    pet.hp = max(0, pet.hp - damage)
                    battle_log += f"{opponent.name}攻击{pet.name}，造成{damage}点伤害！\n"
                else:
                    # 对手攻击
                    damage = opponent.calculate_damage(pet)
                    pet.hp = max(0, pet.hp - damage)
                    battle_log += f"{opponent.name}攻击{pet.name}，造成{damage}点伤害！\n"
                    
                    # 检查玩家是否被击败
                    if not pet.is_alive():
                        battle_log += f"{pet.name}被击败了！\n"
                        break
                    
                    # 玩家攻击
                    damage = pet.calculate_damage(opponent)
                    opponent.hp = max(0, opponent.hp - damage)
                    battle_log += f"{pet.name}攻击{opponent.name}，造成{damage}点伤害！\n"
                
                # 添加分隔线
                battle_log += "-"*20 + "\n"
            
            # 战斗结果
            if pet.is_alive():
                # 玩家获胜
                exp_gain = opponent.level * 20
                pet.exp += exp_gain
                
                # 检查是否升级
                level_up = False
                if pet.exp >= pet.level * 100:
                    pet.level_up()
                    level_up = True
                
                # 更新数据库
                self.db.update_pet_data(
                    user_id,
                    level=pet.level,
                    exp=pet.exp,
                    hp=pet.hp,
                    attack=pet.attack,
                    defense=pet.defense,
                    speed=pet.speed,
                    skills=pet.skills
                )
                
                battle_log += f"\n战斗胜利！{pet.name}获得了{exp_gain}点经验值！"
                if level_up:
                    battle_log += f"\n{pet.name}升级了！"
            else:
                # 玩家失败
                battle_log += f"\n战斗失败！{pet.name}被击败了！"
                
                # 更新数据库
                self.db.update_pet_data(
                    user_id,
                    hp=pet.hp
                )
            
            # 生成对战结果图片
            image_path = await self.img_gen.create_pet_image(battle_log)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                yield event.plain_result(battle_log)
            
        except Exception as e:
            logger.error(f"宠物对战失败: {str(e)}")
            yield event.plain_result("宠物对战失败了~请联系管理员检查日志")
    
    @filter.command("治疗宠物")
    async def heal_pet(self, event: AstrMessageEvent):
        """治疗宠物"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'创建宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 治疗宠物
            result = pet.heal()
            
            # 更新数据库
            self.db.update_pet_data(
                user_id,
                hp=pet.hp,
                hunger=pet.hunger,
                mood=pet.mood
            )
            
            image_path = await self.img_gen.create_pet_image(result)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"治疗宠物失败: {str(e)}")
            yield event.plain_result("治疗宠物失败了~请联系管理员检查日志")

