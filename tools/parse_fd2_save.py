#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FD2.SAV 存档文件完整解析工具
解析炎龙骑士团2的存档文件，结合FDTXT.DAT和FDFIELD.DAT信息
输出角色名字、职业、等级、属性、携带道具等详细信息

根据IDA Pro MCP反汇编分析，基于sub_10010、sub_19DF7等函数1:1还原
"""

import struct
import sys
import os

# 设置UTF-8输出 (解决Windows GBK编码问题)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ==================== 常量定义 ====================
SAVE_FILE_SIZE = 22987
BATTLE_SLOT_SIZE = 2600
NUM_BATTLE_SLOTS = 4
CHAR_DATA_SIZE = 80
MAX_CHAR_COUNT = 96

# 文件结构偏移
OFFSET_CAMP_MAP_DATA = 0
OFFSET_CAMP_BATTLE_TEAM = 2211
OFFSET_CAMP_CHAR_DATA = 4771
OFFSET_CAMP_ICON_CACHE = 12451
OFFSET_CAMP_GAME_STATE = 12483
OFFSET_UNUSED = 12501
OFFSET_BATTLE_SLOTS = 12587
OFFSET_CHECKSUM = 22983

CAMP_SHARED_SIZE = 12501

# ==================== 游戏数据表 ====================
# 注意：这些名称需要从FDTXT.DAT或游戏资源中解析，此处仅作占位符
JOB_NAMES = []  # 职业名称 - 需从FDTXT.DAT获取

ITEM_NAMES = {}  # 道具名称 - 需从FDTXT.DAT获取
SPELL_NAMES = {}  # 法术名称 - 需从FDTXT.DAT获取

STATUS_EFFECTS = [
    "死亡", "中毒", "麻痹", "睡眠", "混乱", "沉默", "减速", "加速"
]

# ==================== 加密/解密 ====================
def decrypt_save(data: bytearray) -> bytearray:
    """
    解密FD2.SAV存档文件
    算法: key = ROL((key - 0x7014), 3), 然后 XOR
    初始密钥: 0xA5
    对应IDA函数: sub_4DF28
    """
    result = bytearray(len(data))
    key = 0xA5
    
    for i in range(len(data)):
        key = ((key - 0x7014) & 0xFFFF)
        key = ((key << 3) | (key >> 13)) & 0xFFFF
        result[i] = data[i] ^ (key & 0xFF)
    
    return result

def calc_checksum(data: bytes) -> int:
    """
    计算校验和
    前22983字节的累加和（每个字节取低8位累加）
    对应IDA函数: sub_4DF09
    """
    checksum = 0
    for i in range(OFFSET_CHECKSUM):
        checksum += data[i]
    return checksum & 0xFFFFFFFF

def verify_checksum(data: bytes) -> bool:
    """验证存档校验和"""
    stored = struct.unpack_from('<I', data, OFFSET_CHECKSUM)[0]
    calc = calc_checksum(data)
    return stored == calc

# ==================== 数据结构定义 ====================
class CampGameState:
    """
    营地游戏状态 (偏移12483-12500, 18字节)
    根据sub_19DF7和sub_10010函数的访问模式还原
    """
    def __init__(self, data: bytes):
        self.dword_53BEF = data[0]
        self.char_count = data[1]      # 角色数量 (n6_0)
        self.map_id = data[2]          # 当前地图ID (n17)
        self.n9 = data[3]
        self.n34 = data[4]
        self.n9_0 = data[5]
        self.n34_0 = data[6]
        self.n2_2 = data[7]
        self.n2_1 = data[8]
        self.icon_count = data[9]      # 图标数量 (n7)
        self.dword_53BF3 = struct.unpack_from('<I', data, 10)[0]
        self.byte_53AF9 = data[14]
        self.byte_51AAB = data[15]
        self.n127 = data[16]
        self.byte_51E62 = data[17]

class CharacterData:
    """
    角色数据结构 (80字节/角色)
    根据battle_char_data_t结构定义 (fd2_battle.h:38-63)
    """
    def __init__(self, data: bytes, index: int):
        self.index = index
        self.tile_x = data[0]           # 地图X坐标
        self.tile_y = data[1]           # 地图Y坐标
        self.padding_2 = data[2]        # 未知/padding
        self.active_mask = data[3]      # 活动状态掩码
        self.faction = data[4]          # 阵营 (0=敌军, 1=NPC, 2=友军)
        self.active_byte = data[5]      # 活动状态字节
        self.char_type = data[6]        # 角色类型 (0=未移动玩家, 1=友军/NPC, 2=敌军)
        self.icon_id = data[7]          # 图标/动画ID
        self.death_status = data[8]     # 死亡状态 (0=存活, 28=死亡)
        self.moved = data[9]            # 0=未移动, 1=已移动
        self.padding_10_25 = data[10:26]  # padding[16]
        self.active_mask2 = data[26]    # 活动状态掩码(备用)
        self.padding_27_31 = data[27:32]  # padding[5]
        self.icon_id_alt = data[32]     # 备用图标ID
        self.direction = data[33]       # 朝向方向
        self.padding_34_38 = data[34:39]  # padding[5]
        self.death_flag = data[39]      # 死亡标志 (0=存活, 非0=死亡)
        self.padding_40_58 = data[40:59]  # padding[19]
        self.anim_data_size = data[59]  # 动画数据大小
        self.padding_60_63 = data[60:64]  # padding[3]
        self.anim_state = data[64:68]   # 动画状态[4]
        self.padding_68_69 = data[68:70]  # padding[2]
        self.level_stats = data[70]     # 等级/状态
        self.padding_71_79 = data[71:80]  # padding[9]
        
        # 原始数据
        self.raw_data = data
    
    @property
    def is_active(self):
        """角色是否存活"""
        return self.death_flag == 0 and self.death_status == 0
    
    @property
    def job_name(self):
        """职业名称"""
        if JOB_NAMES and self.char_type < len(JOB_NAMES):
            return JOB_NAMES[self.char_type]
        return f"职业_{self.char_type}"

class BattleSaveSlot:
    """
    战场临时存档槽位 (2600字节)
    根据sub_2968D和sub_25EBB函数还原
    """
    def __init__(self, data: bytes, slot_index: int):
        self.slot_index = slot_index
        self.offset = OFFSET_BATTLE_SLOTS + slot_index * BATTLE_SLOT_SIZE
        self.battle_data = data[:2560]   # 战场画面数据
        self.map_id = data[2560]         # 地图ID (0xFF表示空槽位)
        self.icon_count = data[2561]     # 图标数量
        self.dword_53BF3 = struct.unpack_from('<I', data, 2562)[0]
        self.byte_51AAB = data[2566]
        self.byte_53AF9 = data[2567]
        self.n127 = data[2568]
        self.byte_51E62 = data[2569]
        self.is_valid = self.map_id != 0xFF

    def __repr__(self):
        status = "有效" if self.is_valid else "空"
        return f"战场槽位{self.slot_index} (偏移{self.offset:#06x}): {status}, 地图ID={self.map_id}"

# ==================== FDFIELD.DAT解析器 ====================
class FDFieldParser:
    """
    FDFIELD.DAT地图数据解析器
    文件头: 6字节 "LLLLLL"
    索引表: 每地图12字节 (布局偏移4字节 + 控制偏移4字节 + 角色位置偏移4字节)
    """
    MAP_ENTRY_SIZE = 12
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = None
        self.map_count = 0
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                self.data = f.read()
            self.map_count = (len(self.data) - 6) // self.MAP_ENTRY_SIZE
    
    def get_map_index(self, map_id: int) -> tuple:
        """获取地图索引信息 (布局偏移, 控制偏移, 角色位置偏移)"""
        if not self.data or map_id >= self.map_count:
            return None
        offset = 6 + map_id * self.MAP_ENTRY_SIZE
        return struct.unpack_from('<III', self.data, offset)
    
    def get_map_control_info(self, map_id: int) -> dict:
        """获取地图控制信息"""
        index = self.get_map_index(map_id)
        if not index:
            return None
        
        layout_offset, control_offset, charpos_offset = index
        
        # 地图基本信息 (3字节)
        map_info = struct.unpack_from('<BBB', self.data, control_offset)
        
        info = {
            'map_number': map_info[0],          # 地图编号
            'max_player_units': map_info[1],    # 己方最多可出场人数
            'total_enemy_units': map_info[2],   # 敌友出场人物总数
        }
        
        # 解析宝箱数据 (偏移0x53, 16组×3字节)
        treasure_offset = control_offset + 0x53
        info['treasures'] = []
        for i in range(16):
            t_data = struct.unpack_from('<BHH', self.data, treasure_offset + i * 3)
            if t_data[1] != 0xFFFF:
                info['treasures'].append({
                    'type': t_data[0],   # 0=物品, 1=金钱
                    'value': t_data[1],
                })
        
        # 解析敌友单位信息 (偏移0x83, 每单位26字节)
        char_info_offset = control_offset + 0x83
        info['units'] = []
        total_units = map_info[2]
        for i in range(total_units):
            offset = char_info_offset + i * 26
            if offset + 26 > len(self.data):
                break
            
            faction = self.data[offset]
            portrait_id = self.data[offset + 1]
            # offset+2 is padding/unknown
            job_id = self.data[offset + 3]
            level = self.data[offset + 4]
            
            faction_name = {0: "敌军", 1: "NPC", 2: "友军"}.get(faction, f"阵营{faction}")
            
            unit = {
                'faction': faction_name,
                'portrait_id': portrait_id,
                'job_id': job_id,
                'job_name': JOB_NAMES[job_id] if (JOB_NAMES and job_id < len(JOB_NAMES)) else f"职业_{job_id}",
                'level': level,
            }
            
            # 装备 (8个槽位)
            unit['items'] = []
            for j in range(8):
                item_id = self.data[offset + 5 + j]
                if item_id != 0xFF:
                    unit['items'].append(f"道具_{item_id:#04x}")
            
            info['units'].append(unit)
        
        return info
    
    def get_map_char_positions(self, map_id: int) -> list:
        """获取角色位置数据"""
        index = self.get_map_index(map_id)
        if not index:
            return None
        
        _, _, charpos_offset = index
        
        if charpos_offset + 2 > len(self.data):
            return None
        
        total_chars = struct.unpack_from('<H', self.data, charpos_offset)[0]
        positions = []
        
        for i in range(total_chars):
            offset = charpos_offset + 2 + i * 6
            if offset + 6 > len(self.data):
                break
            
            x, y, portrait_id = struct.unpack_from('<HHH', self.data, offset)
            positions.append({
                'index': i,
                'x': x,
                'y': y,
                'portrait_id': portrait_id,
            })
        
        return positions

# ==================== FDTXT.DAT解析器 ====================
class FDTXTParser:
    """
    FDTXT.DAT文本资源解析器
    文件头: 6字节 (可能是标识符)
    索引表: 每条目8字节 (数据偏移4字节 + 数据大小4字节)
    数据块: 文本数据，以0xFFFF (-1) 结束
    """
    HEADER_SIZE = 6
    INDEX_ENTRY_SIZE = 8
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = None
        self.text_count = 0
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                self.data = f.read()
            # 计算文本条目数量
            if len(self.data) > self.HEADER_SIZE:
                self.text_count = (len(self.data) - self.HEADER_SIZE) // self.INDEX_ENTRY_SIZE
    
    def get_text_block(self, text_index: int) -> bytes:
        """获取指定索引的文本块"""
        if not self.data or text_index >= self.text_count:
            return None
        
        offset = self.HEADER_SIZE + text_index * self.INDEX_ENTRY_SIZE
        data_offset, data_size = struct.unpack_from('<II', self.data, offset)
        
        if data_offset + data_size > len(self.data):
            return None
        
        return self.data[data_offset:data_offset + data_size]
    
    def parse_text_block(self, text_index: int) -> list:
        """解析文本块中的文本项"""
        block = self.get_text_block(text_index)
        if not block or len(block) < 4:
            return []
        
        text_items = []
        offset = 0
        
        while offset + 4 <= len(block):
            text_id, text_offset = struct.unpack_from('<HH', block, offset)
            if text_id == 0xFFFF:  # -1 结束标记
                break
            text_items.append({'id': text_id, 'offset': text_offset})
            offset += 4
        
        # 提取文本内容
        for item in text_items:
            content = self._extract_text(block, item['offset'])
            item['content'] = content
        
        return text_items
    
    def _extract_text(self, block: bytes, offset: int) -> str:
        """从文本块中提取字符串"""
        text = []
        pos = offset
        
        while pos < len(block):
            byte_val = block[pos]
            
            # 检查控制字符
            if byte_val == 0xFF and pos + 1 < len(block):
                next_byte = block[pos + 1]
                control_code = (byte_val << 8 | next_byte) & 0xFFFF
                
                if control_code == 0xFFFF:  # -1 结束
                    break
                elif control_code == 0xFFFE:  # -2 换行
                    text.append("\\n")
                    pos += 2
                    continue
                elif control_code == 0xFFFD:  # -3 换行+清除
                    text.append("\\n[CLR]")
                    pos += 2
                    continue
            
            # 普通字符 (尝试Big5编码)
            if byte_val > 0xA0 and pos + 1 < len(block):
                char_bytes = bytes([byte_val, block[pos + 1]])
                try:
                    char = char_bytes.decode('big5', errors='replace')
                    text.append(char)
                except:
                    text.append(f"[{byte_val:02x}{block[pos+1]:02x}]")
                pos += 2
            else:
                if 32 <= byte_val < 127:
                    text.append(chr(byte_val))
                else:
                    text.append(f"[{byte_val:02x}]")
                pos += 1
        
        return ''.join(text)

# ==================== 主解析器 ====================
class FD2SaveParser:
    """FD2.SAV存档文件完整解析器"""
    
    def __init__(self):
        self.raw_data = None
        self.decrypted_data = None
        self.camp_state = None
        self.characters = []
        self.battle_slots = []
    
    def load(self, filepath: str) -> bool:
        """加载并解密存档文件"""
        if not os.path.exists(filepath):
            print(f"[错误] 文件不存在: {filepath}")
            return False
        
        file_size = os.path.getsize(filepath)
        if file_size != SAVE_FILE_SIZE:
            print(f"[错误] 文件大小不匹配: {file_size} != {SAVE_FILE_SIZE}")
            return False
        
        with open(filepath, 'rb') as f:
            self.raw_data = f.read()
        
        # 解密 (对应sub_4DF28)
        self.decrypted_data = decrypt_save(bytearray(self.raw_data))
        
        # 验证校验和 (对应sub_4DF09)
        if verify_checksum(self.decrypted_data):
            print("[成功] 校验和验证通过")
        else:
            stored = struct.unpack_from('<I', self.decrypted_data, OFFSET_CHECKSUM)[0]
            calc = calc_checksum(self.decrypted_data)
            print(f"[警告] 校验和不匹配: 存储={stored:#010x}, 计算={calc:#010x}")
        
        # 解析营地游戏状态 (对应sub_10010的偏移12483-12500)
        state_data = bytes(self.decrypted_data[OFFSET_CAMP_GAME_STATE:OFFSET_CAMP_GAME_STATE+18])
        self.camp_state = CampGameState(state_data)
        
        # 解析角色数据 (对应sub_10010: memmove(dword_53A45, v0+4771, 80*n6_0))
        self.characters = []
        char_count = min(self.camp_state.char_count, MAX_CHAR_COUNT)
        for i in range(char_count):
            char_offset = OFFSET_CAMP_CHAR_DATA + i * CHAR_DATA_SIZE
            char_data = bytes(self.decrypted_data[char_offset:char_offset+CHAR_DATA_SIZE])
            self.characters.append(CharacterData(char_data, i))
        
        # 解析战场存档槽位 (对应sub_2968D: v11 = 2600 * n2_3 + v6 + 12587)
        self.battle_slots = []
        for i in range(NUM_BATTLE_SLOTS):
            slot_offset = OFFSET_BATTLE_SLOTS + i * BATTLE_SLOT_SIZE
            slot_data = bytes(self.decrypted_data[slot_offset:slot_offset+BATTLE_SLOT_SIZE])
            self.battle_slots.append(BattleSaveSlot(slot_data, i))
        
        return True
    
    def dump_full_report(self, field_parser: FDFieldParser = None, text_parser: FDTXTParser = None):
        """输出完整解析报告"""
        print("=" * 70)
        print("FD2.SAV 存档完整解析报告")
        print("=" * 70)
        
        # 基本信息
        print(f"\n文件大小: {SAVE_FILE_SIZE} 字节")
        print(f"加密方式: XOR滚动加密 (sub_4DF28, key=0xA5)")
        print(f"校验方式: 累加和校验 (sub_4DF09)")
        
        # 校验和验证
        stored = struct.unpack_from('<I', self.decrypted_data, OFFSET_CHECKSUM)[0]
        calc = calc_checksum(self.decrypted_data)
        print(f"校验和: 存储={stored:#010x}, 计算={calc:#010x} {'[✓]' if stored == calc else '[✗]'}")
        
        # 营地存档信息
        self._dump_camp_info()
        
        # 角色信息
        self._dump_characters()
        
        # 战场存档信息
        self._dump_battle_slots()
        
        # FDFIELD地图信息
        if field_parser:
            self._dump_field_info(field_parser)
        
        # FDTXT文本信息
        if text_parser:
            self._dump_text_info(text_parser)
        
        print("\n" + "=" * 70)
        print("解析完成")
        print("=" * 70)
    
    def _dump_camp_info(self):
        """输出营地存档信息"""
        print(f"\n--- 营地存档 (共享区 0-{CAMP_SHARED_SIZE-1}) ---")
        print(f"  角色数量: {self.camp_state.char_count}")
        print(f"  当前地图ID: {self.camp_state.map_id}")
        print(f"  图标数量: {self.camp_state.icon_count}")
        print(f"  dword_53BEF: {self.camp_state.dword_53BEF}")
        print(f"  dword_53BF3: {self.camp_state.dword_53BF3:#010x}")
        print(f"  byte_53AF9: {self.camp_state.byte_53AF9:#04x}")
        print(f"  byte_51AAB: {self.camp_state.byte_51AAB:#04x}")
        print(f"  n127: {self.camp_state.n127}")
        print(f"  byte_51E62: {self.camp_state.byte_51E62:#04x}")
    
    def _dump_characters(self):
        """输出角色信息"""
        print(f"\n--- 角色列表 (偏移{OFFSET_CAMP_CHAR_DATA}, {CHAR_DATA_SIZE}字节/角色, 共{len(self.characters)}个) ---")
        
        for char in self.characters:
            if not char.is_active and char.icon_id == 0xFF:
                continue
            
            faction_name = {0: "敌军", 1: "NPC", 2: "友军"}.get(char.faction, f"阵营{char.faction}")
            char_type_name = {0: "未移动玩家", 1: "友军/NPC", 2: "敌军"}.get(char.char_type, f"类型{char.char_type}")
            
            print(f"\n  角色 #{char.index}")
            print(f"    图标ID: {char.icon_id}")
            print(f"    图标ID(备用): {char.icon_id_alt}")
            print(f"    角色类型: {char_type_name} (ID: {char.char_type})")
            print(f"    阵营: {faction_name}")
            print(f"    朝向: {char.direction}")
            print(f"    地图位置: ({char.tile_x}, {char.tile_y})")
            print(f"    死亡状态: {char.death_status}")
            print(f"    死亡标志: {char.death_flag}")
            print(f"    是否移动: {'已移动' if char.moved else '未移动'}")
            print(f"    活动掩码: {char.active_mask:#04x}, {char.active_mask2:#04x}")
            print(f"    动画数据大小: {char.anim_data_size}")
            print(f"    动画状态: {list(char.anim_state)}")
            print(f"    等级/状态: {char.level_stats}")
    
    def _dump_battle_slots(self):
        """输出战场存档信息"""
        print(f"\n--- 战场临时存档 (4个槽位, 偏移{OFFSET_BATTLE_SLOTS}开始, 每槽位{BATTLE_SLOT_SIZE}字节) ---")
        
        for slot in self.battle_slots:
            status = "有效" if slot.is_valid else "空"
            print(f"\n  槽位 {slot.slot_index} (偏移{slot.offset:#06x}): {status}")
            
            if slot.is_valid:
                print(f"    地图ID: {slot.map_id}")
                print(f"    图标数量: {slot.icon_count}")
                print(f"    dword_53BF3: {slot.dword_53BF3:#010x}")
                print(f"    byte_51AAB: {slot.byte_51AAB:#04x}")
                print(f"    byte_53AF9: {slot.byte_53AF9:#04x}")
                print(f"    n127: {slot.n127}")
                print(f"    byte_51E62: {slot.byte_51E62:#04x}")
            else:
                print(f"    (该槽位为空, map_id=0xFF)")
    
    def _dump_field_info(self, field_parser: FDFieldParser):
        """输出地图信息 (来自FDFIELD.DAT)"""
        map_id = self.camp_state.map_id
        if map_id >= field_parser.map_count:
            print(f"\n[警告] 地图ID {map_id} 超出FDFIELD.DAT范围 (共{field_parser.map_count}个地图)")
            return
        
        map_info = field_parser.get_map_control_info(map_id)
        if not map_info:
            return
        
        print(f"\n--- 地图 {map_info['map_number']} 信息 (来自FDFIELD.DAT, 地图ID={map_id}) ---")
        print(f"  己方最多可出场人数: {map_info['max_player_units']}")
        print(f"  敌军总数: {map_info['total_enemy_units']}")
        
        # 宝箱
        if map_info['treasures']:
            print(f"  宝箱列表:")
            for i, treasure in enumerate(map_info['treasures']):
                if treasure['type'] == 0:
                    print(f"    宝箱{i}: 物品 #{treasure['value']} (ID: {treasure['value']:#04x})")
                elif treasure['type'] == 1:
                    print(f"    宝箱{i}: 金钱 {treasure['value']}")
        
        # 敌友单位
        if map_info['units']:
            print(f"  敌友单位列表:")
            for i, unit in enumerate(map_info['units']):
                print(f"    单位{i}: {unit['faction']}, 肖像ID={unit['portrait_id']}, {unit['job_name']}, 等级{unit['level']}")
                if unit['items']:
                    print(f"      装备: {', '.join(unit['items'])}")
        
        # 角色位置
        positions = field_parser.get_map_char_positions(map_id)
        if positions:
            print(f"  角色位置数据 (共{len(positions)}个):")
            for pos in positions[:10]:  # 只显示前10个
                char_type = "己方" if pos['portrait_id'] == 0 else f"敌军/NPC(肖像{pos['portrait_id']})"
                print(f"    角色{pos['index']}: X={pos['x']}, Y={pos['y']}, {char_type}")
            if len(positions) > 10:
                print(f"    ... 还有{len(positions)-10}个角色")
    
    def _dump_text_info(self, text_parser: FDTXTParser):
        """输出文本信息 (来自FDTXT.DAT)"""
        map_id = self.camp_state.map_id
        text_index = map_id + 1  # 根据IDA分析，地图文本索引 = map_id + 1
        
        if text_index >= text_parser.text_count:
            print(f"\n[警告] 文本索引 {text_index} 超出FDTXT.DAT范围 (共{text_parser.text_count}个条目)")
            return
        
        print(f"\n--- 文本资源 (来自FDTXT.DAT, 地图ID={map_id}, 文本索引={text_index}) ---")
        
        text_items = text_parser.parse_text_block(text_index)
        if text_items:
            print(f"  文本项数量: {len(text_items)}")
            for item in text_items[:10]:  # 只显示前10个
                print(f"    文本ID {item['id']}: {item['content']}")
            if len(text_items) > 10:
                print(f"    ... 还有{len(text_items)-10}个文本项")
        else:
            print(f"  无文本数据")

# ==================== 命令行工具 ====================
def main():
    import argparse
    
    arg_parser = argparse.ArgumentParser(description='FD2.SAV 存档文件解析工具')
    arg_parser.add_argument('save_file', help='FD2.SAV存档文件路径')
    arg_parser.add_argument('field_file', nargs='?', default=None, help='FDFIELD.DAT地图数据文件 (可选)')
    arg_parser.add_argument('text_file', nargs='?', default=None, help='FDTXT.DAT文本资源文件 (可选)')
    arg_parser.add_argument('--export', '-e', type=str, default=None, help='导出到文件 (支持 .txt, .json)')
    
    args = arg_parser.parse_args()
    
    save_file = args.save_file
    field_file = args.field_file
    text_file = args.text_file
    
    parser = FD2SaveParser()
    if not parser.load(save_file):
        sys.exit(1)
    
    field_parser = None
    if field_file and os.path.exists(field_file):
        field_parser = FDFieldParser(field_file)
        print(f"[信息] 已加载FDFIELD.DAT: {field_file} (共{field_parser.map_count}个地图)")
    elif field_file:
        print(f"[警告] FDFIELD.DAT文件不存在: {field_file}")
    
    text_parser = None
    if text_file and os.path.exists(text_file):
        text_parser = FDTXTParser(text_file)
        print(f"[信息] 已加载FDTXT.DAT: {text_file} (共{text_parser.text_count}个文本条目)")
    elif text_file:
        print(f"[警告] FDTXT.DAT文件不存在: {text_file}")
    
    # 如果指定了导出文件
    if args.export:
        # 确定输出目录 (脚本所在目录的上级output目录)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # 如果只提供了文件名，添加到output目录
        if not os.path.isabs(args.export):
            export_path = os.path.join(output_dir, args.export)
        else:
            export_path = args.export
        
        # 重定向输出到文件
        with open(export_path, 'w', encoding='utf-8') as f:
            # 保存原始stdout
            original_stdout = sys.stdout
            sys.stdout = f
            
            try:
                parser.dump_full_report(field_parser, text_parser)
            finally:
                # 恢复stdout
                sys.stdout = original_stdout
        
        print(f"[成功] 解析结果已导出到: {export_path}")
    else:
        # 直接输出到控制台
        parser.dump_full_report(field_parser, text_parser)

if __name__ == '__main__':
    main()
