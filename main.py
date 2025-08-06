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
                    "草": "藤甲虫",
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

            # 解析文本信息
            lines = text.split('\n')
            pet_info = {}
            for line in lines:
                if '：' in line:
                    key, value = line.split('：', 1)
                    pet_info[key] = value

            # 绘制信息卡排版
            # 主人信息
            if '主人' in pet_info:
                draw.text((400, 150), f"主人：{pet_info['主人']}", font=font_text, fill=(0, 0, 0))
            
            # 宠物名称
            if '名称' in pet_info:
                draw.text((400, 200), f"名称：{pet_info['名称']}", font=font_text, fill=(0, 0, 0))
            
            # 宠物属性
            if '属性' in pet_info:
                draw.text((400, 250), f"属性：{pet_info['属性']}", font=font_text, fill=(0, 0, 0))
            
            # 战力值
            if '战力值' in pet_info:
                draw.text((400, 300), f"战力值：{pet_info['战力值']}", font=font_text, fill=(0, 0, 0))
            
            # 等级
            if '等级' in pet_info:
                draw.text((400, 350), f"等级：{pet_info['等级']}", font=font_text, fill=(0, 0, 0))

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


@register("宠物", "Tinyxi", "一个QQ宠物插件，包含创建宠物、喂养、对战等功能", "1.0.0", "https://github.com/520TinyXI/chongwu.git")
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
    
    @filter.command("领取宠物")
    async def adopt_pet(self, event: AstrMessageEvent, pet_type: str = None, pet_name: str = None):
        """领取宠物"""
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
            logger.info(f"用户 {user_id} 请求领取宠物")
            
            # 双重检查是否已领养宠物
            if user_id in self.pets or self.db.get_pet_data(user_id):
                yield event.plain_result("您已经领取了宠物！")
                return
            
            # 预设宠物名称和类型
            pet_options = [
                {"name": "烈焰", "type": "火"},
                {"name": "碧波兽", "type": "水"},
                {"name": "藤甲虫", "type": "草"},
                {"name": "碎裂岩", "type": "土"},
                {"name": "金刚", "type": "金"}
            ]
            
            # 获取发送者名称
            sender_name = event.get_sender_name() or "未知"
            
            if pet_type and pet_name:
                # 检查属性是否有效
                valid_types = ["火", "水", "草", "土", "金"]
                if pet_type not in valid_types:
                    yield event.plain_result(f"无效的属性！请选择：{', '.join(valid_types)}")
                    return
                
                # 检查是否是预设名称
                matched_pet = next((p for p in pet_options if p["name"] == pet_name and p["type"] == pet_type), None)
                if matched_pet:
                    pet = Pet(matched_pet["name"], matched_pet["type"], sender_name)
                else:
                    # 自定义名称
                    pet = Pet(pet_name, pet_type, sender_name)
            else:
                # 如果没有提供属性和名称，提示正确的指令格式
                yield event.plain_result("正确的领取指令：/领取宠物 属性 名字\n属性可选：火、水、草、土、金")
                return
            
            self.pets[user_id] = pet
            
            # 保存到数据库
            self.db.create_pet(user_id, pet.name, pet.type, pet.owner)
            self.db.update_pet_data(user_id, **pet.to_dict())
            
            # 生成结果信息
            result = f"成功领取宠物！！！\n名称：{pet.name}\n属性：{pet.type}\n等级：{pet.level}\n经验值：{pet.exp}/{pet.get_exp_required(pet.level)}\n数值：\nHP={pet.hp},攻击={pet.attack}\n防御={pet.defense},速度={pet.speed}\n技能：无"
            
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
            logger.error(f"领取宠物失败: {str(e)}")
            yield event.plain_result(f"领取宠物失败了~错误原因: {str(e)}")

    @filter.command("宠物进化")
    async def evolve_pet(self, event: AstrMessageEvent):
        """宠物进化"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有领取宠物！请先使用'领取宠物'命令")
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
            image_path = await self.img_gen.create_pet_image(result, pet.type)
            if image_path:
                yield event.image_result(image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
            else:
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
                yield event.plain_result("您还没有领取宠物！请先使用'领取宠物'命令")
                return
            
            # 检查对手是否存在宠物
            if opponent_id not in self.pets and not self.db.get_pet_data(opponent_id):
                yield event.plain_result(f"对手{opponent_id}还没有领取宠物！")
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
            
            # 决定先手（速度高者先攻，速度相同则随机）
            speed_diff = abs(pet.speed - opponent_pet.speed)
            speed_advantage = speed_diff * 0.004  # 每点速度差增加0.4%先手概率
            
            if pet.speed > opponent_pet.speed:
                player_first = random.random() < (0.5 + speed_advantage)
            elif pet.speed < opponent_pet.speed:
                player_first = random.random() >= (0.5 + speed_advantage)
            else:
                # 速度相同则随机决定先手
                player_first = random.choice([True, False])
            
            while pet.is_alive() and opponent_pet.is_alive():
                if player_first:
                    # 玩家攻击
                    # 30%概率使用技能
                    if random.random() < 0.3 and pet.skills:
                        skill = random.choice(pet.skills)
                        if skill == "火球术":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了火球术！\n"
                        elif skill == "水枪术":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了水枪术！\n"
                        elif skill == "藤鞭":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了藤鞭！\n"
                        elif skill == "地震":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了地震！\n"
                        elif skill == "金属爪":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了金属爪！\n"
                        elif skill == "烈焰风暴":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了烈焰风暴！\n"
                        elif skill == "水龙卷":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了水龙卷！\n"
                        elif skill == "飞叶快刀":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了飞叶快刀！\n"
                        elif skill == "岩崩":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了岩崩！\n"
                        elif skill == "雷电拳":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了雷电拳！\n"
                        else:
                            skill_multiplier = 1.0
                    else:
                        skill_multiplier = 1.0
                    
                    damage = pet.calculate_damage(opponent_pet, skill_multiplier)
                    opponent_pet.hp = max(0, opponent_pet.hp - damage)
                    battle_log += f"{pet.name}攻击{opponent_pet.name}，造成{damage}点伤害！\n"
                    
                    # 检查对手是否被击败
                    if not opponent_pet.is_alive():
                        battle_log += f"{opponent_pet.name}被击败了！\n"
                        break
                    
                    # 对手攻击
                    # 30%概率使用技能
                    if random.random() < 0.3 and opponent_pet.skills:
                        skill = random.choice(opponent_pet.skills)
                        if skill == "火球术":
                            skill_multiplier = 1.2
                            battle_log += f"{opponent_pet.name}使用了火球术！\n"
                        elif skill == "水枪术":
                            skill_multiplier = 1.2
                            battle_log += f"{opponent_pet.name}使用了水枪术！\n"
                        elif skill == "藤鞭":
                            skill_multiplier = 1.2
                            battle_log += f"{opponent_pet.name}使用了藤鞭！\n"
                        elif skill == "地震":
                            skill_multiplier = 1.2
                            battle_log += f"{opponent_pet.name}使用了地震！\n"
                        elif skill == "金属爪":
                            skill_multiplier = 1.2
                            battle_log += f"{opponent_pet.name}使用了金属爪！\n"
                        elif skill == "烈焰风暴":
                            skill_multiplier = 1.5
                            battle_log += f"{opponent_pet.name}使用了烈焰风暴！\n"
                        elif skill == "水龙卷":
                            skill_multiplier = 1.5
                            battle_log += f"{opponent_pet.name}使用了水龙卷！\n"
                        elif skill == "飞叶快刀":
                            skill_multiplier = 1.5
                            battle_log += f"{opponent_pet.name}使用了飞叶快刀！\n"
                        elif skill == "岩崩":
                            skill_multiplier = 1.5
                            battle_log += f"{opponent_pet.name}使用了岩崩！\n"
                        elif skill == "雷电拳":
                            skill_multiplier = 1.5
                            battle_log += f"{opponent_pet.name}使用了雷电拳！\n"
                        else:
                            skill_multiplier = 1.0
                    else:
                        skill_multiplier = 1.0
                    
                    damage = opponent_pet.calculate_damage(pet, skill_multiplier)
                    pet.hp = max(0, pet.hp - damage)
                    battle_log += f"{opponent_pet.name}攻击{pet.name}，造成{damage}点伤害！\n"
                else:
                    # 对手攻击
                    # 30%概率使用技能
                    if random.random() < 0.3 and opponent_pet.skills:
                        skill = random.choice(opponent_pet.skills)
                        if skill in ["火球术", "水枪术", "藤鞭", "地震", "金属爪"]:
                            skill_multiplier = 1.2
                            battle_log += f"{opponent_pet.name}使用了{skill}！\n"
                        elif skill in ["烈焰风暴", "水龙卷", "飞叶快刀", "岩崩", "雷电拳"]:
                            skill_multiplier = 1.5
                            battle_log += f"{opponent_pet.name}使用了{skill}！\n"
                        else:
                            skill_multiplier = 1.0
                    else:
                        skill_multiplier = 1.0
                    
                    damage = opponent_pet.calculate_damage(pet, skill_multiplier)
                    pet.hp = max(0, pet.hp - damage)
                    battle_log += f"{opponent_pet.name}攻击{pet.name}，造成{damage}点伤害！\n"
                    
                    # 检查玩家是否被击败
                    if not pet.is_alive():
                        battle_log += f"{pet.name}被击败了！\n"
                        break
                    
                    # 玩家攻击
                    # 30%概率使用技能
                    if random.random() < 0.3 and pet.skills:
                        skill = random.choice(pet.skills)
                        if skill in ["火球术", "水枪术", "藤鞭", "地震", "金属爪"]:
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了{skill}！\n"
                        elif skill in ["烈焰风暴", "水龙卷", "飞叶快刀", "岩崩", "雷电拳"]:
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了{skill}！\n"
                        else:
                            skill_multiplier = 1.0
                    else:
                        skill_multiplier = 1.0
                    
                    damage = pet.calculate_damage(opponent_pet, skill_multiplier)
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
                if pet.exp >= pet.get_exp_required(pet.level):
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
/宠物进化 - 当宠物达到指定等级后进化
/对决 @某人 - 与其他玩家进行PVP对战（每30分钟冷却）
/治疗宠物 - 治疗受伤的宠物
/宠物大全 - 显示游戏内所有宠物
/宠物菜单 - 显示此帮助菜单
/查看金币 - 查看当前拥有的金币数量
/商店 - 查看商店可购买的物品
/购买 [物品ID] - 购买商店中的物品
/投喂 [物品名] - 给宠物使用背包中的物品
/查看技能 - 查看宠物已学习的技能
/使用技能 [技能名] - 在对战中使用宠物技能

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
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 更新宠物状态
            pet.update_status()
            
            # 保存到数据库
            self.db.update_pet_data(user_id, **pet.to_dict())
            
            # 直接返回纯文字结果，不生成图片
            result = str(pet)
            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"查看宠物失败: {str(e)}")
            yield event.plain_result("查看宠物失败了~请联系管理员检查日志")
    
    @filter.command("宠物大全")
    async def pet_catalog(self, event: AstrMessageEvent):
        """显示所有预设宠物"""
        try:
            # 预设宠物名称和类型
            pet_options = [
                {"name": "烈焰", "type": "火"},
                {"name": "碧波兽", "type": "水"},
                {"name": "藤甲虫", "type": "草"},
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


    @filter.command("购买")
    async def buy_item(self, event: AstrMessageEvent, item_name: str = None, quantity: int = 1):
        """购买物品"""
        try:
            user_id = event.get_sender_id()
            
            # 检查参数
            if not item_name:
                yield event.plain_result("请使用格式: /购买 [物品名] [数量]")
                return
            
            # 获取商店物品
            shop_items = self.db.get_shop_items()
            item = next((i for i in shop_items if i["name"] == item_name), None)
            
            if not item:
                yield event.plain_result(f"商店中没有{item_name}！")
                return
            
            # 检查数量
            if quantity <= 0:
                yield event.plain_result("购买数量必须大于0！")
                return
            
            # 计算总价
            total_price = item["price"] * quantity
            
            # 检查是否有足够的金币
            if user_id in self.pets:
                pet = self.pets[user_id]
                if pet.coins < total_price:
                    yield event.plain_result(f"金币不足！您需要{total_price}金币，但只有{pet.coins}金币。")
                    return
                
                # 扣除金币
                pet.coins -= total_price
                # 更新数据库
                self.db.update_pet_data(user_id, coins=pet.coins)
            
            # 添加物品到背包
            self.db.add_item_to_inventory(user_id, item_name, quantity)
            
            yield event.plain_result(f"成功购买{quantity}个{item_name}，花费{total_price}金币！您还剩余{pet.coins}金币。")
            
        except Exception as e:
            logger.error(f"购买物品失败: {str(e)}")
            yield event.plain_result("购买物品失败了~请联系管理员检查日志")
    
    async def battle_pet(self, event: AstrMessageEvent, pet: Pet, opponent_pet: Pet, user_id: str, opponent_name: str) -> dict:
        """与对手宠物进行战斗"""
        try:
            # 检查宠物是否存活
            if not pet.is_alive():
                return {"result": "lose", "message": f"{pet.name}已经失去战斗能力，请先治疗！"}
            
            if not opponent_pet.is_alive():
                return {"result": "lose", "message": f"对手的{opponent_pet.name}已经失去战斗能力！"}
            
            # 对战过程
            battle_log = f"{pet.name} vs {opponent_pet.name}\n" + "="*30 + "\n"
            
            # 决定先手（速度高者先攻，速度相同则随机）
            speed_diff = abs(pet.speed - opponent_pet.speed)
            speed_advantage = speed_diff * 0.004  # 每点速度差增加0.4%先手概率
            
            if pet.speed > opponent_pet.speed:
                player_first = random.random() < (0.5 + speed_advantage)
            elif pet.speed < opponent_pet.speed:
                player_first = random.random() >= (0.5 + speed_advantage)
            else:
                # 速度相同则随机决定先手
                player_first = random.choice([True, False])
            
            while pet.is_alive() and opponent_pet.is_alive():
                if player_first:
                    # 玩家攻击
                    # 30%概率使用技能
                    if random.random() < 0.3 and pet.skills:
                        skill = random.choice(pet.skills)
                        if skill == "火球术":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了火球术！\n"
                        elif skill == "水枪术":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了水枪术！\n"
                        elif skill == "藤鞭":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了藤鞭！\n"
                        elif skill == "地震":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了地震！\n"
                        elif skill == "金属爪":
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了金属爪！\n"
                        elif skill == "烈焰风暴":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了烈焰风暴！\n"
                        elif skill == "水龙卷":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了水龙卷！\n"
                        elif skill == "飞叶快刀":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了飞叶快刀！\n"
                        elif skill == "岩崩":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了岩崩！\n"
                        elif skill == "雷电拳":
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了雷电拳！\n"
                        else:
                            skill_multiplier = 1.0
                    else:
                        skill_multiplier = 1.0
                    
                    damage = pet.calculate_damage(opponent_pet, skill_multiplier)
                    opponent_pet.hp = max(0, opponent_pet.hp - damage["damage"])
                    battle_log += f"{pet.name}攻击{opponent_pet.name}，造成{damage['damage']}点伤害！\n"
                    
                    # 检查对手是否被击败
                    if not opponent_pet.is_alive():
                        battle_log += f"{opponent_pet.name}被击败了！\n"
                        break
                    
                    # 对手攻击
                    # 30%概率使用技能
                    if random.random() < 0.3 and opponent_pet.skills:
                        skill = random.choice(opponent_pet.skills)
                        if skill in ["火球术", "水枪术", "藤鞭", "地震", "金属爪"]:
                            skill_multiplier = 1.2
                            battle_log += f"{opponent_pet.name}使用了{skill}！\n"
                        elif skill in ["烈焰风暴", "水龙卷", "飞叶快刀", "岩崩", "雷电拳"]:
                            skill_multiplier = 1.5
                            battle_log += f"{opponent_pet.name}使用了{skill}！\n"
                        else:
                            skill_multiplier = 1.0
                    else:
                        skill_multiplier = 1.0
                    
                    damage = opponent_pet.calculate_damage(pet, skill_multiplier)
                    pet.hp = max(0, pet.hp - damage["damage"])
                    battle_log += f"{opponent_pet.name}攻击{pet.name}，造成{damage['damage']}点伤害！\n"
                else:
                    # 对手攻击
                    # 30%概率使用技能
                    if random.random() < 0.3 and opponent_pet.skills:
                        skill = random.choice(opponent_pet.skills)
                        if skill in ["火球术", "水枪术", "藤鞭", "地震", "金属爪"]:
                            skill_multiplier = 1.2
                            battle_log += f"{opponent_pet.name}使用了{skill}！\n"
                        elif skill in ["烈焰风暴", "水龙卷", "飞叶快刀", "岩崩", "雷电拳"]:
                            skill_multiplier = 1.5
                            battle_log += f"{opponent_pet.name}使用了{skill}！\n"
                        else:
                            skill_multiplier = 1.0
                    else:
                        skill_multiplier = 1.0
                    
                    damage = opponent_pet.calculate_damage(pet, skill_multiplier)
                    pet.hp = max(0, pet.hp - damage["damage"])
                    battle_log += f"{opponent_pet.name}攻击{pet.name}，造成{damage['damage']}点伤害！\n"
                    
                    # 检查玩家是否被击败
                    if not pet.is_alive():
                        battle_log += f"{pet.name}被击败了！\n"
                        break
                    
                    # 玩家攻击
                    # 30%概率使用技能
                    if random.random() < 0.3 and pet.skills:
                        skill = random.choice(pet.skills)
                        if skill in ["火球术", "水枪术", "藤鞭", "地震", "金属爪"]:
                            skill_multiplier = 1.2
                            battle_log += f"{pet.name}使用了{skill}！\n"
                        elif skill in ["烈焰风暴", "水龙卷", "飞叶快刀", "岩崩", "雷电拳"]:
                            skill_multiplier = 1.5
                            battle_log += f"{pet.name}使用了{skill}！\n"
                        else:
                            skill_multiplier = 1.0
                    else:
                        skill_multiplier = 1.0
                    
                    damage = pet.calculate_damage(opponent_pet, skill_multiplier)
                    opponent_pet.hp = max(0, opponent_pet.hp - damage["damage"])
                    battle_log += f"{pet.name}攻击{opponent_pet.name}，造成{damage['damage']}点伤害！\n"
                
                # 添加分隔线
                battle_log += "-"*20 + "\n"
            
            # 战斗结果
            if pet.is_alive():
                # 玩家获胜
                return {"result": "win", "message": battle_log}
            else:
                # 玩家失败
                return {"result": "lose", "message": battle_log}
        except Exception as e:
            logger.error(f"宠物战斗失败: {str(e)}")
            return {"result": "error", "message": "宠物战斗失败了~请联系管理员检查日志"}
    
    @filter.command("探索")
    async def explore(self, event: AstrMessageEvent):
        """探索功能"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 生成随机事件
            event_type = random.random()
            
            if event_type < 0.05:  # 5%机缘事件
                # 隐士高人事件
                gold = random.randint(100, 1000)
                exp = 500
                
                # 增加金币
                pet.coins += gold
                
                # 增加宠物经验
                pet.exp += exp
                
                # 检查是否升级
                level_up = False
                if pet.exp >= pet.get_exp_required(pet.level):
                    pet.level_up()
                    level_up = True
                
                # 更新数据库
                self.db.update_pet_data(
                    user_id,
                    coins=pet.coins,
                    exp=pet.exp,
                    level=pet.level,
                    hp=pet.hp,
                    attack=pet.attack,
                    defense=pet.defense,
                    speed=pet.speed,
                    skills=pet.skills
                )
                
                result = f"遇到了隐士高人，赠与金币{gold}并传授你的宠物{exp}经验值！"
                if level_up:
                    result += f"\n{pet.name}升级了！"
            
            elif event_type < 0.20:  # 15%好事件
                good_event_type = random.randint(1, 3)
                
                if good_event_type == 1:  # 医疗箱事件
                    heal_bottles = random.randint(1, 10)
                    self.db.add_item_to_inventory(user_id, "中治疗瓶", heal_bottles)
                    result = f"路上捡到了医疗箱，打开后发现{heal_bottles}瓶中治疗瓶！"
                elif good_event_type == 2:  # 老太太事件
                    exp = 500
                    pet.exp += exp
                    
                    # 检查是否升级
                    level_up = False
                    if pet.exp >= pet.get_exp_required(pet.level):
                        pet.level_up()
                        level_up = True
                    
                    # 更新数据库
                    self.db.update_pet_data(
                        user_id,
                        exp=pet.exp,
                        level=pet.level,
                        hp=pet.hp,
                        attack=pet.attack,
                        defense=pet.defense,
                        speed=pet.speed,
                        skills=pet.skills
                    )
                    
                    result = f"碰到了一个老太太，她见你骨骼精奇，给你宠物传授了{exp}经验值！"
                    if level_up:
                        result += f"\n{pet.name}升级了！"
                elif good_event_type == 3:  # 小女孩事件
                    cans = random.randint(10, 15)
                    self.db.add_item_to_inventory(user_id, "美味罐头", cans)
                    result = f"一个小女孩撞到了你，她给你道歉后送你美味罐头{cans}个！"
            
            else:  # 80%坏事件
                bad_event_type = random.randint(1, 7)
                opponent_level = pet.level  # 对手等级与宠物等级相同
                
                # 随机选择对手属性（金木水火土）
                opponent_types = ["金", "木", "水", "火", "土"]
                opponent_type = random.choice(opponent_types)
                
                # 根据事件类型设置对手名称
                opponent_names = {
                    1: "邪恶训练师",
                    2: "陷阱哥布林",
                    3: "魔灵兔",
                    4: "狸龙",
                    5: "持刀人",
                    6: "饿狼",
                    7: "棕熊"
                }
                opponent_name = opponent_names[bad_event_type]
                
                # 创建对手宠物
                opponent_pet = Pet(opponent_name, opponent_type)
                opponent_pet.level = opponent_level
                opponent_pet.update_stats()  # 更新对手属性
                
                # 设置事件描述
                if bad_event_type == 1:
                    event_desc = f"碰到了{opponent_name}【{opponent_level}级】\n你不得不和他对战！！！"
                elif bad_event_type == 2:
                    # 掉入陷阱，减少HP
                    hp_loss = random.randint(10, 20)
                    pet.hp = max(1, pet.hp - hp_loss)  # 确保不会死亡
                    self.db.update_pet_data(user_id, hp=pet.hp)
                    event_desc = f"你掉进了陷阱！！HP值减少{hp_loss}！\n遇到了{opponent_name}【{opponent_level}级】"
                elif bad_event_type == 3:
                    event_desc = f"你看见了一只发疯的{opponent_name}【{opponent_level}级】，你准备为民除害！！"
                elif bad_event_type == 4:
                    event_desc = f"你在家中睡觉，梦境中遇到了{opponent_name}【{opponent_level}级】，开始对战"
                elif bad_event_type == 5:
                    event_desc = f"路上一个鬼鬼祟祟的人，你叫住他，他掏出刀子准备和你对战，注意，他的等级是【{opponent_level}级】"
                elif bad_event_type == 6:
                    event_desc = f"一群{opponent_name}【{opponent_level}级】挡住了去路，他们眼中泛着绿光，看来只能战斗了！"
                elif bad_event_type == 7:
                    event_desc = f"山洞中惊醒了沉睡的{opponent_name}【{opponent_level}级】，它对你穷追不舍！"
                
                # 开始战斗
                battle_result = await self.battle_pet(event, pet, opponent_pet, user_id, "未知")
                
                # 检查战斗结果
                if pet.is_alive():  # 玩家胜利
                    # 计算奖励
                    exp_reward = random.randint(20, 35) * pet.level
                    gold_reward = random.randint(80, 168)
                    
                    # 增加奖励
                    pet.exp += exp_reward
                    pet.coins += gold_reward
                    
                    # 检查是否升级
                    level_up = False
                    if pet.exp >= pet.get_exp_required(pet.level):
                        pet.level_up()
                        level_up = True
                    
                    # 更新数据库
                    self.db.update_pet_data(
                        user_id,
                        hp=pet.hp,
                        exp=pet.exp,
                        coins=pet.coins,
                        level=pet.level,
                        attack=pet.attack,
                        defense=pet.defense,
                        speed=pet.speed,
                        skills=pet.skills
                    )
                    
                    result = f"{event_desc}\n\n战斗胜利！\n获得经验值：{exp_reward}，金币：{gold_reward}"
                    if level_up:
                        result += f"\n{pet.name}升级了！"
                else:  # 玩家失败
                    # 失败惩罚：损失部分金币（最多100金币）
                    gold_loss = min(100, pet.coins // 10)  # 损失10%金币，最多100
                    pet.coins = max(0, pet.coins - gold_loss)
                    
                    # 更新数据库
                    self.db.update_pet_data(user_id, coins=pet.coins)
                    
                    result = f"{event_desc}\n\n战斗失败！\n损失金币：{gold_loss}"
            
            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"探索失败: {str(e)}")
            yield event.plain_result("探索失败了~请联系管理员检查日志")
    
    @filter.command("宠物背包")
    async def pet_inventory(self, event: AstrMessageEvent):
        """查看宠物背包"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 获取用户背包
            inventory = self.db.get_user_inventory(user_id)
            
            # 生成背包列表
            inventory_list = "您的背包\n"
            inventory_list += "--------------------\n"
            inventory_list += "代币背包\n"
            inventory_list += f"金币数量：{pet.coins}\n"
            inventory_list += "--------------------\n"
            inventory_list += "物品背包\n"
            
            # 检查物品背包是否为空
            has_items = False
            for item in inventory:
                if item['quantity'] > 0:  # 只显示数量大于0的物品
                    inventory_list += f"{item['name']}: {item['quantity']}\n"
                    has_items = True
            
            if not has_items:
                inventory_list += "您的物品背包空空如也\n"
            
            yield event.plain_result(inventory_list)
            
        except Exception as e:
            logger.error(f"查看宠物背包失败: {str(e)}")
            yield event.plain_result("查看宠物背包失败了~请联系管理员检查日志")
    
    @filter.command("投喂")
    async def feed_pet(self, event: AstrMessageEvent, item_name: str = None):
        """投喂宠物"""
        try:
            user_id = event.get_sender_id()
            
            # 检查参数
            if not item_name:
                yield event.plain_result("请使用格式: /投喂 [物品名]")
                return
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 检查背包中是否有该物品
            inventory = self.db.get_user_inventory(user_id)
            item_found = False
            for item in inventory:
                if item['name'] == item_name and item['quantity'] > 0:
                    item_found = True
                    break
            
            if not item_found:
                yield event.plain_result(f"您的背包中没有{item_name}！")
                return
            
            # 使用物品
            result = self.db.use_item_on_pet(user_id, item_name, pet)
            
            # 更新数据库
            self.db.update_pet_data(
                user_id,
                hp=pet.hp,
                hunger=pet.hunger,
                mood=pet.mood
            )
            
            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"投喂宠物失败: {str(e)}")
            yield event.plain_result("投喂宠物失败了~请联系管理员检查日志")
    
    @filter.command("查看技能")
    async def check_skills(self, event: AstrMessageEvent):
        """查看宠物技能"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 返回技能列表
            if pet.skills:
                skills_list = "、".join(pet.skills)
                yield event.plain_result(f"{pet.name}已学习的技能：{skills_list}")
            else:
                yield event.plain_result(f"{pet.name}还没有学习任何技能！")
            
        except Exception as e:
            logger.error(f"查看技能失败: {str(e)}")
            yield event.plain_result("查看技能失败了~请联系管理员检查日志")
    
    @filter.command("使用技能")
    async def use_skill(self, event: AstrMessageEvent, skill_name: str = None):
        """使用技能"""
        try:
            user_id = event.get_sender_id()
            
            # 检查参数
            if not skill_name:
                yield event.plain_result("请使用格式: /使用技能 [技能名]")
                return
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 检查宠物是否拥有该技能
            if skill_name not in pet.skills:
                yield event.plain_result(f"{pet.name}没有学习过{skill_name}技能！")
                return
            
            # 使用技能（这里可以添加具体的技能效果逻辑）
            result = f"{pet.name}使用了{skill_name}技能！"
            
            # 根据技能类型添加效果
            if skill_name in ['金刃', '火焰冲击', '水炮', '藤鞭', '地震']:
                result += "\n技能效果：造成额外伤害！"
            elif skill_name in ['坚固', '大地守护']:
                result += "\n技能效果：提升防御力！"
            elif skill_name in ['光合作用', '水雾']:
                result += "\n技能效果：恢复少量HP！"
            elif skill_name in ['燃烧', '冰冻']:
                result += "\n技能效果：使对手进入异常状态！"
            elif skill_name in ['反射', '寄生种子']:
                result += "\n技能效果：反弹部分伤害或持续恢复HP！"
            elif skill_name in ['破甲', '沙尘暴']:
                result += "\n技能效果：降低对手防御或命中率！"
            elif skill_name in ['金属风暴', '熔岩爆发', '海啸', '森林祝福', '地裂']:
                result += "\n技能效果：强大的范围攻击技能！"
            else:
                result += "\n技能效果：发挥出了不错的效果！"
            
            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"使用技能失败: {str(e)}")
            yield event.plain_result("使用技能失败了~请联系管理员检查日志")
    
    @filter.command("商店")
    async def shop(self, event: AstrMessageEvent):
        """查看商店物品"""
        try:
            # 获取商店物品列表
            items = self.db.get_shop_items()
            
            if not items:
                yield event.plain_result("商店暂时没有物品出售！")
                return
            
            # 生成商店列表
            shop_list = "欢迎来到宠物商店！\n"
            shop_list += "物品列表：\n"
            for item in items:
                shop_list += f"{item['id']}. {item['name']} - {item['price']}金币\n"
                shop_list += f"   {item['description']}\n\n"
            
            shop_list += "购买物品请使用: /购买 [物品ID]"
            
            yield event.plain_result(shop_list)
            
        except Exception as e:
            logger.error(f"查看商店失败: {str(e)}")
            yield event.plain_result("查看商店失败了~请联系管理员检查日志")
    
    @filter.command("购买")
    async def buy_item(self, event: AstrMessageEvent, item_id: str = None):
        """购买商店物品"""
        try:
            user_id = event.get_sender_id()
            
            # 检查参数
            if not item_id:
                yield event.plain_result("请使用格式: /购买 [物品ID]")
                return
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 获取商店物品
            items = self.db.get_shop_items()
            item = None
            for i in items:
                if str(i['id']) == item_id:
                    item = i
                    break
            
            if not item:
                yield event.plain_result("无效的物品ID！")
                return
            
            # 检查金币是否足够
            if pet.coins < item['price']:
                yield event.plain_result(f"金币不足！您需要{item['price']}金币来购买{item['name']}。")
                return
            
            # 扣除金币
            pet.coins -= item['price']
            
            # 添加物品到背包
            self.db.add_item_to_inventory(user_id, item['name'], 1)
            
            # 更新数据库
            self.db.update_pet_data(user_id, coins=pet.coins)
            
            yield event.plain_result(f"成功购买{item['name']}！花费了{item['price']}金币，剩余金币：{pet.coins}")
            
        except Exception as e:
            logger.error(f"购买物品失败: {str(e)}")
            yield event.plain_result("购买物品失败了~请联系管理员检查日志")
    
    @filter.command("战斗设置")
    async def battle_settings(self, event: AstrMessageEvent):
        """查看战斗设置"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 返回战斗设置
            settings = f"战斗中血量低于【{pet.auto_heal_threshold}】自动使用治疗瓶\n提示：如需修改数值，输入/修改最低血量 [数值]。如果不使用治疗瓶填入0即可"
            yield event.plain_result(settings)
            
        except Exception as e:
            logger.error(f"查看战斗设置失败: {str(e)}")
            yield event.plain_result("查看战斗设置失败了~请联系管理员检查日志")
    
    @filter.command("修改最低血量")
    async def modify_auto_heal_threshold(self, event: AstrMessageEvent, threshold: int = None):
        """修改自动使用治疗瓶的最低血量阈值"""
        try:
            user_id = event.get_sender_id()
            
            # 检查参数
            if threshold is None:
                yield event.plain_result("请使用格式: /修改最低血量 [数值]")
                return
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 更新阈值
            pet.auto_heal_threshold = threshold
            
            # 更新数据库
            self.db.update_pet_data(user_id, auto_heal_threshold=pet.auto_heal_threshold)
            
            # 返回结果
            yield event.plain_result(f"已将自动使用治疗瓶的最低血量阈值修改为{threshold}")
            
        except Exception as e:
            logger.error(f"修改最低血量失败: {str(e)}")
            yield event.plain_result("修改最低血量失败了~请联系管理员检查日志")
    
    @filter.command("宠物背包")
    async def pet_inventory(self, event: AstrMessageEvent):
        """查看宠物背包"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 获取用户背包物品
            inventory = self.db.get_user_inventory(user_id)
            
            # 生成背包信息
            result = "您的背包\n"
            result += "--------------------\n"
            result += "代币背包\n"
            result += f"金币数量：{pet.coins}\n"
            result += "--------------------\n"
            result += "物品背包\n"
            
            if inventory:
                for item in inventory:
                    result += f"{item['name']} x{item['quantity']}\n"
            else:
                result += "您的物品背包空空如也"
            
            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"查看宠物背包失败: {str(e)}")
            yield event.plain_result("查看宠物背包失败了~请联系管理员检查日志")
    
    @filter.command("宠物详细")
    async def pet_details(self, event: AstrMessageEvent):
        """显示宠物的详细信息"""
        try:
            user_id = event.get_sender_id()
            
            # 检查是否有宠物
            if user_id not in self.pets:
                yield event.plain_result("您还没有创建宠物！请先使用'领取宠物'命令")
                return
            
            pet = self.pets[user_id]
            
            # 更新宠物状态
            pet.update_status()
            
            # 生成宠物详细信息
            details = "您的宠物数值：\n"
            details += f"战力值：{pet.attack + pet.defense + pet.speed}\n"
            details += f"等级：{pet.level}\n"
            details += f"经验值：{pet.exp}/{pet.get_exp_required(pet.level)}\n"
            details += f"生命值：{pet.hp}\n"
            details += f"攻击力：{pet.attack}\n"
            details += f"防御力：{pet.defense}\n"
            details += f"速度：{pet.speed}\n"
            details += f"暴击率：{pet.critical_rate:.1%}\n"
            details += f"暴击伤害：{pet.critical_damage:.0%}\n"
            details += f"技能：{', '.join(pet.skills) if pet.skills else '无'}"
            
            # 更新数据库
            self.db.update_pet_data(
                user_id,
                hp=pet.hp,
                hunger=pet.hunger,
                mood=pet.mood
            )
            
            yield event.plain_result(details)
            
        except Exception as e:
            logger.error(f"显示宠物详细信息失败: {str(e)}")
            yield event.plain_result("显示宠物详细信息失败了~请联系管理员检查日志")

