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
from .pet import Pet, PetDatabase

# PetImageGenerator类
class PetImageGenerator:
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.bg_image = os.path.join(plugin_dir, "assets", "background.png")
        self.font_path = os.path.join(plugin_dir, "assets", "font.ttf")
        self.output_dir = os.path.join(plugin_dir, "temp")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 检查并修复背景图片
        self._check_and_fix_background()
    
    def _check_and_fix_background(self):
        """检查并修复背景图片"""
        try:
            # 检查背景图片是否存在且有效
            if os.path.exists(self.bg_image):
                # 尝试打开背景图片
                img = Image.open(self.bg_image)
                img.verify()  # 验证图片完整性
                print(f"背景图片正常: {self.bg_image}")
                return
        except Exception as e:
            print(f"背景图片损坏或无法打开: {e}")
        
        # 创建新的背景图片
        self._create_new_background()
    
    def _create_new_background(self):
        """创建新的背景图片"""
        # 确保assets目录存在
        assets_dir = os.path.join(self.plugin_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
        
        # 创建纯白色背景
        W, H = 800, 600
        bg = Image.new('RGB', (W, H), (255, 255, 255))  # 纯白色
        
        # 保存背景图片
        bg.save(self.bg_image)
        print(f"新的背景图片已创建: {self.bg_image}")

    async def create_pet_image(self, text: str, pet_type: str = None, font_size: int = 36) -> Union[str, None]:
        """生成宠物信息图片"""
        try:
            # 调整背景图片大小为800x600
            W, H = 800, 600
            bg = Image.open(self.bg_image)
            bg = bg.resize((W, H))

            draw = ImageDraw.Draw(bg)

            # 设置字体
            try:
                if os.path.exists(self.font_path):
                    font_title = ImageFont.truetype(self.font_path, 40)
                    font_text = ImageFont.truetype(self.font_path, 28)
                else:
                    font_title = ImageFont.load_default()
                    font_text = ImageFont.load_default()
            except Exception:
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()

            # 如果提供了宠物类型，尝试添加宠物图片
            # 首先检查pet_type是否直接在TYPE_IMAGES中
            pet_image_name = None
            if pet_type and pet_type in Pet.TYPE_IMAGES:
                pet_image_name = Pet.TYPE_IMAGES[pet_type]
            # 如果没有找到，尝试通过属性克制关系映射
            elif pet_type and pet_type in Pet.TYPE_ADVANTAGES:
                # 根据属性类型映射到具体的宠物名称
                type_to_name = {
                    "火": "烈焰",
                    "水": "碧波兽",
                    "草": "莲莲草",
                    "土": "碎裂岩",
                    "金": "金刚"
                }
                pet_name = type_to_name.get(pet_type)
                if pet_name and pet_name in Pet.TYPE_IMAGES:
                    pet_image_name = Pet.TYPE_IMAGES[pet_name]
            
            if pet_image_name:
                pet_image_path = os.path.join(os.path.dirname(self.bg_image), f"{pet_image_name}.png")
                if os.path.exists(pet_image_path):
                    try:
                        pet_img = Image.open(pet_image_path).convert("RGBA")
                        # 调整宠物图片大小
                        pet_img = pet_img.resize((300, 300))
                        # 将宠物图片粘贴到背景图片上(左侧)
                        bg.paste(pet_img, (50, 150), pet_img)
                    except Exception as e:
                        print(f"加载宠物图片失败: {e}")
                        import traceback
                        traceback.print_exc()

            # 绘制标题(居中)
            title = "宠物信息卡"
            draw.text((W / 2, 50), title, font=font_title, fill=(0, 0, 0), anchor="mt")

            # 绘制文本信息(右侧)
            lines = text.split('\n')
            y_offset = 150
            line_spacing = 40  # 增加行间距
            
            # 绘制文本信息(右侧)
            for line in lines:
                draw.text((400, y_offset), line, font=font_text, fill=(0, 0, 0))
                y_offset += line_spacing

            output_path = os.path.join(self.output_dir, f"pet_{int(datetime.now().timestamp())}.png")
            bg.save(output_path)
            print(f"图片已保存到: {output_path}")
            return output_path
        except Exception as e:
            print(f"生成图片失败: {e}")
            import traceback
            traceback.print_exc()
            return None

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
    
    @filter.command("领养宠物")
    async def adopt_pet(self, event: AstrMessageEvent, pet_name: str = None):
        """领养宠物"""
        try:
            # 处理可能缺失的参数
            if event is None:
                # 创建模拟事件对象
                class MockEvent:
                    def __init__(self):
                        self.user_id = "test_user"
                        self.args = []
                    def get_sender_id(self):
                        return self.user_id
                    def get_args(self):
                        return self.args
                    def plain_result(self, text):
                        return text
                    def image_result(self, image_path):
                        return f"[图片] {image_path}"
                event = MockEvent()
            
            user_id = event.get_sender_id()
            logger.info(f"用户 {user_id} 请求领养宠物")
            
            # 双重检查是否已领养宠物
            if user_id in self.pets or self.db.get_pet_data(user_id):
                yield event.plain_result("您已经领养了宠物！")
                return
            
            # 预设宠物名称和类型
            pet_options = [
                {"name": "烈焰", "type": "火"},
                {"name": "碧波兽", "type": "水"},
                {"name": "莲莲草", "type": "草"},
                {"name": "碎裂岩", "type": "土"},
                {"name": "金刚", "type": "金"}
            ]
            
            if pet_name:
                # 检查是否是预设名称
                matched_pet = next((p for p in pet_options if p["name"] == pet_name), None)
                if matched_pet:
                    pet = Pet(matched_pet["name"], matched_pet["type"])
                else:
                    # 自定义名称，随机类型
                    random_pet = random.choice(pet_options)
                    pet = Pet(pet_name, random_pet["type"])
            else:
                # 如果没有提供名称，提示正确的指令格式
                yield event.plain_result("正确的领养指令：/领养宠物 【名字】")
                return
            
            self.pets[user_id] = pet
            
            # 保存到数据库
            self.db.create_pet(user_id, pet.name, pet.type)
            self.db.update_pet_data(user_id, **pet.to_dict())
            
            # 生成结果信息
            result = f"成功领养宠物！！！\n名称：{pet.name}\n属性：{pet.type}\n等级：{pet.level}\n经验值：{pet.exp}/{pet.level * 100}\n数值：\nHP={pet.hp},攻击={pet.attack}\n防御={pet.defense},速度={pet.speed}\n技能：无"
            
            # 尝试生成图片
            try:
                image_path = await self.img_gen.create_pet_image(result, pet.type)
                if image_path:
                    yield event.image_result(image_path)
                    # 延迟删除临时文件，避免文件被占用
                    import asyncio
                    await asyncio.sleep(1)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                else:
                    yield event.plain_result(result)
            except Exception as e:
                logger.error(f"生成图片失败: {str(e)}")
                yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"领养宠物失败: {str(e)}")
            yield event.plain_result(f"领养宠物失败了~错误原因: {str(e)}")

    @filter.command("宠物进化")
    async def evolve_pet(self, event: AstrMessageEvent):
        """宠物进化"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有领养宠物！请先使用'领养宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 检查是否可以进化
            if not pet.can_evolve():
                yield event.plain_result(f"{pet.name}还不能进化！需要达到{Pet.EVOLUTION_DATA.get(pet.name, {}).get('required_level', 10)}级")
                return
            
            # 执行进化
            result = pet.evolve()
            
            # 更新数据库
            self.db.update_pet_data(
                user_id,
                pet_name=pet.name,
                pet_type=pet.type,
                level=pet.level,
                exp=pet.exp,
                hp=pet.hp,
                attack=pet.attack,
                defense=pet.defense,
                speed=pet.speed,
                skills=pet.skills
            )
            
            # 生成进化结果图片
            # 直接返回纯文字结果，不生成图片
            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"宠物进化失败: {str(e)}")
            yield event.plain_result("宠物进化失败了~请联系管理员检查日志")

    @filter.command("我的宠物")
    async def my_pet(self, event: AstrMessageEvent):
        """生成宠物状态卡"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有领养宠物！请先使用'领养宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 更新宠物状态
            pet.update_status()
            
            # 保存到数据库
            self.db.update_pet_data(user_id, **pet.to_dict())
            
            # 生成状态卡图片
            result = str(pet)
            image_path = await self.img_gen.create_pet_image(result, pet.type)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"生成状态卡失败: {str(e)}")
            yield event.plain_result("生成状态卡失败了~请联系管理员检查日志")

    @filter.command("对决")
    async def duel_pet(self, event: AstrMessageEvent, opponent_id: str):
        """与其他玩家进行PVP对战"""
        try:
            user_id = event.get_sender_id()
            
            # 检查参数
            if not opponent_id:
                yield event.plain_result("请使用格式: /对决 @某人")
                return
            
            # 解析对手ID（这里简化处理，实际可能需要从@提及中提取）
            opponent_id = opponent_id.replace("@", "")
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有领养宠物！请先使用'领养宠物'命令")
                return
            
            # 检查对手是否存在宠物
            if opponent_id not in self.pets and not self.db.get_pet_data(opponent_id):
                yield event.plain_result(f"对手{opponent_id}还没有领养宠物！")
                return
            
            # 加载对手宠物
            if opponent_id not in self.pets:
                pet_data = self.db.get_pet_data(opponent_id)
                if pet_data:
                    self.pets[opponent_id] = Pet.from_dict(pet_data)
                else:
                    yield event.plain_result(f"无法加载对手{opponent_id}的宠物数据！")
                    return
            
            pet = self.pets[user_id]
            opponent_pet = self.pets[opponent_id]
            
            # 检查宠物是否存活
            if not pet.is_alive():
                yield event.plain_result(f"{pet.name}已经失去战斗能力，请先治疗！")
                return
            
            if not opponent_pet.is_alive():
                yield event.plain_result(f"对手的{opponent_pet.name}已经失去战斗能力，请等待对手治疗后再挑战！")
                return
            
            # 检查冷却时间
            if not pet.is_battle_available():
                yield event.plain_result(f"{pet.name}还在冷却中，请30分钟后再进行对决！")
                return
            
            # 对战过程
            battle_log = f"{pet.name} vs {opponent_pet.name}\n" + "="*30 + "\n"
            
            # 决定先手
            player_first = pet.speed >= opponent_pet.speed
            
            while pet.is_alive() and opponent_pet.is_alive():
                if player_first:
                    # 玩家攻击
                    damage = pet.calculate_damage(opponent_pet)
                    opponent_pet.hp = max(0, opponent_pet.hp - damage)
                    battle_log += f"{pet.name}攻击{opponent_pet.name}，造成{damage}点伤害！\n"
                    
                    # 检查对手是否被击败
                    if not opponent_pet.is_alive():
                        battle_log += f"{opponent_pet.name}被击败了！\n"
                        break
                    
                    # 对手攻击
                    damage = opponent_pet.calculate_damage(pet)
                    pet.hp = max(0, pet.hp - damage)
                    battle_log += f"{opponent_pet.name}攻击{pet.name}，造成{damage}点伤害！\n"
                else:
                    # 对手攻击
                    damage = opponent_pet.calculate_damage(pet)
                    pet.hp = max(0, pet.hp - damage)
                    battle_log += f"{opponent_pet.name}攻击{pet.name}，造成{damage}点伤害！\n"
                    
                    # 检查玩家是否被击败
                    if not pet.is_alive():
                        battle_log += f"{pet.name}被击败了！\n"
                        break
                    
                    # 玩家攻击
                    damage = pet.calculate_damage(opponent_pet)
                    opponent_pet.hp = max(0, opponent_pet.hp - damage)
                    battle_log += f"{pet.name}攻击{opponent_pet.name}，造成{damage}点伤害！\n"
                
                # 添加分隔线
                battle_log += "-"*20 + "\n"
            
            # 更新对战时间
            pet.update_battle_time()
            
            # 战斗结果
            if pet.is_alive():
                # 玩家获胜
                exp_gain = opponent_pet.level * 15
                pet.exp += exp_gain
                
                # 检查是否升级
                level_up = False
                if pet.exp >= pet.level * 100:
                    pet.level_up()
                    level_up = True
                
                battle_log += f"\n战斗胜利！{pet.name}获得了{exp_gain}点经验值！"
                if level_up:
                    battle_log += f"\n{pet.name}升级了！"
            else:
                # 玩家失败
                battle_log += f"\n战斗失败！{pet.name}被击败了！"
                
            # 更新数据库
            self.db.update_pet_data(
                user_id,
                level=pet.level,
                exp=pet.exp,
                hp=pet.hp,
                attack=pet.attack,
                defense=pet.defense,
                speed=pet.speed,
                skills=pet.skills,
                last_battle_time=pet.last_battle_time.isoformat()
            )
            
            self.db.update_pet_data(
                opponent_id,
                hp=opponent_pet.hp
            )
            
            # 直接返回纯文字结果，不生成图片
            yield event.plain_result(battle_log)
            
        except Exception as e:
            logger.error(f"宠物对决失败: {str(e)}")
            yield event.plain_result("宠物对决失败了~请联系管理员检查日志")

    @filter.command("宠物菜单")
    async def pet_menu(self, event: AstrMessageEvent):
        """显示宠物帮助菜单"""
        try:
            menu = """宠物系统帮助菜单

/领养宠物 [名称] - 领养一只宠物，可指定名称
/我的宠物 - 查看宠物状态卡
/训练宠物 - 训练宠物获得经验
/宠物进化 - 当宠物达到指定等级后进化
/宠物对战 - 与野生宠物对战
/对决 @某人 - 与其他玩家进行PVP对战（每30分钟冷却）
/治疗宠物 - 治疗受伤的宠物
/宠物大全 - 显示游戏内所有宠物
/宠物菜单 - 显示此帮助菜单

属性克制关系:
金克木 | 木克土 | 土克水 | 水克火 | 火克金
克制目标伤害增幅20%"""
            
            # 直接返回纯文字结果，不生成图片
            yield event.plain_result(menu)
            
        except Exception as e:
            logger.error(f"显示宠物菜单失败: {str(e)}")
            yield event.plain_result("显示宠物菜单失败了~请联系管理员检查日志")
    
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
            
            # 生成状态卡图片
            result = str(pet)
            image_path = await self.img_gen.create_pet_image(result, pet.type)
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
            
            # 直接返回纯文字结果，不生成图片
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
            
            image_path = await self.img_gen.create_pet_image(result, pet.type)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
                yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"治疗宠物失败: {str(e)}")
            yield event.plain_result("治疗宠物失败了~请联系管理员检查日志")
    
    @filter.command("宠物大全")
    async def pet_catalog(self, event: AstrMessageEvent):
        """显示所有预设宠物"""
        try:
            # 预设宠物名称和类型
            pet_options = [
                {"name": "烈焰", "type": "火"},
                {"name": "碧波兽", "type": "水"},
                {"name": "莲莲草", "type": "草"},
                {"name": "碎裂岩", "type": "土"},
                {"name": "金刚", "type": "金"}
            ]
            
            # 生成宠物列表
            pet_list = "\n".join([f"【{pet['name']}】 {pet['type']}" for pet in pet_options])
            result = f"游戏内所有宠物:\n{pet_list}"
            
            # 直接返回纯文字结果，不生成图片
            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"显示宠物大全失败: {str(e)}")
            yield event.plain_result("显示宠物大全失败了~请联系管理员检查日志")

