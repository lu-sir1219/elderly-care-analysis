import pandas as pd
import numpy as np

# 读取“各省老年人人数及健康情况.xlsx”

df_elderly = pd.read_excel('E:/Project/PythonProject1/各省老年人人数及健康情况.xlsx', engine='openpyxl')
df_elderly['不能自理总人数'] = df_elderly['生活不能自理男'] + df_elderly['生活不能自理女']
df_elderly_core = df_elderly[['地区', '60岁及以上合计', '不能自理总人数']].copy()

#  读取“全国各地区一人户统计.xlsx”
df_one_person = pd.read_excel('E:/Project/PythonProject1/全国各地区一人户统计.xlsx', engine='openpyxl')
df_one_person_core = df_one_person[['地区', '一人户']].copy()

# 读取“各省养老资源.xlsx”
df_institution = pd.read_excel('E:/Project/PythonProject1/各省养老资源.xlsx', engine='openpyxl')
df_institution_core = df_institution[['地区', '养老机构']].copy()

#  按“地区”列合并3个表
# 合并老年人口表和一人户表
df_merge1 = pd.merge(
    df_elderly_core,
    df_one_person_core,
    on='地区',
    how='inner'
)
# 合并养老资源表
df_merge2 = pd.merge(
    df_merge1,
    df_institution_core,
    on='地区',
    how='inner'
)

# 计算“每万老人机构数”
df_merge2['每万老人机构数（个/万人）'] = (
    df_merge2['养老机构'] / (df_merge2['60岁及以上合计'] / 10000)
).round(2)

# 整理最终表格
df_final = df_merge2[
    ['地区', '60岁及以上合计', '不能自理总人数', '一人户', '每万老人机构数（个/万人）']
].rename(columns={
    '60岁及以上合计': '60岁及以上老年人口',
    '不能自理总人数': '不能自理人数',
    '一人户': '一人户人数'
})

# 保存
df_final.to_excel(
    'E:/Project/PythonProject1/全国各省市老年人口状况调查.xlsx',
    index=False,  # 不保留行号，表格更整洁
    engine='openpyxl'
)
