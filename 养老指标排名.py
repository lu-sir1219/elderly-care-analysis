import pandas as pd
import numpy as np

file_path = 'E:/Project/PythonProject1/全国各省市老年人口状况调查.xlsx'
df = pd.read_excel(file_path, engine='openpyxl')

# 2. 计算2个关键占比指标
df['失能占比（%）'] = (df['不能自理人数'] / df['60岁及以上老年人口'] * 100).round(2)
df['一人户占老年人口比（%）'] = (df['一人户人数'] / df['60岁及以上老年人口'] * 100).round(2)

# 3. 指标标准化
def normalize_positive(series):
    """正向指标标准化：数值越高，得分越高"""
    return ((series - series.min()) / (series.max() - series.min()) * 100).round(2)

def normalize_negative(series):
    """反向指标标准化：数值越低，得分越高（每万老人机构数）"""
    return ((series.max() - series) / (series.max() - series.min()) * 100).round(2)

# 各指标标准化得分
df['失能占比标准化得分'] = normalize_positive(df['失能占比（%）'])  # 正向：失能越高，得分越高
df['老年人口标准化得分'] = normalize_positive(df['60岁及以上老年人口'])  # 正向：人口越多，得分越高
df['一人户标准化得分'] = normalize_positive(df['一人户占老年人口比（%）'])  # 正向：独居相关占比越高，得分越高
df['机构数标准化得分'] = normalize_negative(df['每万老人机构数（个/万人）'])  # 反向：机构越少，得分越高

# 4. 计算综合得分
df['养老需求综合得分'] = (
    df['失能占比标准化得分'] * 0.35 +
    df['机构数标准化得分'] * 0.30 +
    df['老年人口标准化得分'] * 0.25 +
    df['一人户标准化得分'] * 0.10
).round(2)

# 5. 按综合得分降序排名
df_ranked = df.sort_values('养老需求综合得分', ascending=False).reset_index(drop=True)
df_ranked['需求优先级排名'] = df_ranked.index + 1  # 排名从1开始

# 6. 整理最终排名表
final_ranking = df_ranked[
    ['需求优先级排名', '地区', '60岁及以上老年人口', '不能自理人数', '失能占比（%）',
     '一人户人数', '每万老人机构数（个/万人）', '养老需求综合得分']
].copy()

# 7. 保存排名结果到原文件夹
save_path = 'E:/Project/PythonProject1/各省养老需求优先级排名.xlsx'
final_ranking.to_excel(save_path, index=False, engine='openpyxl')
