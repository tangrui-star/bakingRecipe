import pandas as pd
import re
import os
from datetime import datetime

# 读取Excel文件
file_path = r'C:\Users\tangrui\Desktop\中通对接\物流(45).xlsx'
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_path = os.path.join(
    os.path.dirname(file_path),
    f'处理后的物流信息_{timestamp}.xlsx'
)

print("正在读取Excel文件...")
df = pd.read_excel(file_path)

print(f"共{len(df)}条记录需要处理")

# 定义输出数据的列表
result_data = []

# 解析函数
def parse_logistics_info(text):
    """
    解析物流信息文本
    格式示例：26\n收货信息：姓名 手机号\n地址行1\n地址行2...
    """
    if pd.isna(text):
        return {}
    
    text = str(text).strip()
    
    # 初始化结果字典
    result = {
        '订单号': '',
        '代收金额': '',
        '收件人姓名': '',
        '收件人手机': '',
        '收件人电话': '',
        '收件人地址': '',
        '收件人单位': '',
        '品名': '',
        '数量': '',
        '买家备注': '',
        '卖家备注': ''
    }
    
    # 按换行符分割
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        return result
    
    # 第一行通常是订单号
    first_line = lines[0].strip()
    # 尝试提取订单号（可能是纯数字）
    order_match = re.search(r'^(\d+)', first_line)
    if order_match:
        result['订单号'] = "";
    
    # 查找包含"收货信息"的行
    receiver_info_line = None
    receiver_info_idx = -1
    for idx, line in enumerate(lines):
        if '收货信息' in line or '收件信息' in line:
            receiver_info_line = line
            receiver_info_idx = idx
            break
    
    if receiver_info_line:
        # 解析收货信息：姓名 手机号
        # 格式：收货信息：姓名 手机号
        info_match = re.search(r'收货信息[：:]\s*(.+?)\s+(\d{11})', receiver_info_line)
        if not info_match:
            # 尝试另一种格式：姓名 手机号（没有"收货信息："前缀）
            info_match = re.search(r'([^\d]+?)\s+(\d{11})', receiver_info_line)
        
        if info_match:
            name = info_match.group(1).strip()
            phone = info_match.group(2).strip()
            result['收件人姓名'] = name
            result['收件人手机'] = phone
            result['收件人电话'] = phone  # 根据示例，手机和电话相同
            
            # 从收货信息行中提取地址（如果手机号后面还有内容）
            remaining_text = receiver_info_line[receiver_info_line.find(phone) + len(phone):].strip()
            if remaining_text:
                # 如果剩余文本看起来像地址（包含省市区等关键词）
                if any(keyword in remaining_text for keyword in ['省', '市', '区', '县', '镇', '乡', '街道', '路', '号']):
                    address_parts = [remaining_text]
                else:
                    address_parts = []
            else:
                address_parts = []
        
        # 地址信息通常在收货信息行的后面
        address_lines = []
        for idx in range(receiver_info_idx + 1, len(lines)):
            line = lines[idx].strip()
            # 跳过空行和明显不是地址的行（如包含"品名"、"数量"等关键词）
            if line and not re.search(r'品名|数量|备注|代收金额', line):
                address_lines.append(line)
        
        # 合并地址信息
        if 'address_parts' in locals():
            address_lines = address_parts + address_lines
        
        if address_lines:
            result['收件人地址'] = ' '.join(address_lines).replace(' ', '')
    
    else:
        # 如果没有找到"收货信息"标记，尝试从第一行开始解析
        # 格式可能是：订单号 收货信息：姓名 手机号 地址
        # 或者：订单号\n姓名 手机号\n地址
        if len(lines) >= 2:
            # 尝试从第二行提取姓名和手机号
            second_line = lines[1]
            name_phone_match = re.search(r'([^\d]+?)\s+(\d{11})', second_line)
            if name_phone_match:
                result['收件人姓名'] = name_phone_match.group(1).strip()
                phone = name_phone_match.group(2).strip()
                result['收件人手机'] = phone
                result['收件人电话'] = phone
            
            # 剩余行作为地址
            if len(lines) > 2:
                address_lines = [line.strip() for line in lines[2:] if line.strip()]
                result['收件人地址'] = ' '.join(address_lines).replace(' ', '')
    
    # 尝试提取其他信息（代收金额、品名、数量、备注等）
    full_text = text
    # 代收金额
    amount_match = re.search(r'代收[金额]?[：:]?\s*(\d+\.?\d*)', full_text)
    if amount_match:
        result['代收金额'] = amount_match.group(1)
    
    # 品名
    product_match = re.search(r'品名[：:]?\s*(.+?)(?:\n|数量|$)', full_text)
    if product_match:
        result['品名'] = product_match.group(1).strip()
    
    # 数量
    quantity_match = re.search(r'数量[：:]?\s*(\d+)', full_text)
    if quantity_match:
        result['数量'] = quantity_match.group(1)
    
    # 买家备注
    buyer_note_match = re.search(r'买家备注[：:]?\s*(.+?)(?:\n|卖家备注|$)', full_text)
    if buyer_note_match:
        result['买家备注'] = buyer_note_match.group(1).strip()
    
    # 卖家备注
    seller_note_match = re.search(r'卖家备注[：:]?\s*(.+?)(?:\n|$)', full_text)
    if seller_note_match:
        result['卖家备注'] = seller_note_match.group(1).strip()
    
    return result

# 处理每一行数据
for idx, row in df.iterrows():
    print(f"正在处理第 {idx + 1}/{len(df)} 条记录...")
    text = row.iloc[0]  # 第一列的数据
    parsed = parse_logistics_info(text)
    result_data.append(parsed)

# 创建DataFrame
result_df = pd.DataFrame(result_data)

# 确保列的顺序
column_order = ['订单号', '代收金额', '收件人姓名', '收件人手机', '收件人电话', 
                '收件人地址', '收件人单位', '品名', '数量', '买家备注', '卖家备注']
result_df = result_df[column_order]

# 保存到新的Excel文件
print(f"\n正在保存到 {output_path}...")
result_df.to_excel(output_path, index=False, engine='openpyxl')
print(f"处理完成！共处理 {len(result_df)} 条记录")
print(f"\n结果预览（前5条）:")
print(result_df.head())
