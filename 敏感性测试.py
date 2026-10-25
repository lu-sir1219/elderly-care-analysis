import pandas as pd
import numpy as np

# 数据加载
file_path = 'E:/Project/PythonProject1/各省养老需求优先级排名.xlsx'
df = pd.read_excel(file_path, engine='openpyxl')

# 补充计算一人户占比
df['一人户占老年人口比（%）'] = (df['一人户人数'] / df['60岁及以上老年人口'] * 100).round(2)


# 标准化函数
def normalize_positive(series):
    return ((series - series.min()) / (series.max() - series.min()) * 100).round(2)


def normalize_negative(series):
    return ((series.max() - series) / (series.max() - series.min()) * 100).round(2)


# 计算标准化得分（
df['失能占比标准化得分'] = normalize_positive(df['失能占比（%）'])
df['老年人口标准化得分'] = normalize_positive(df['60岁及以上老年人口'])
df['一人户标准化得分'] = normalize_positive(df['一人户占老年人口比（%）'])
df['机构数标准化得分'] = normalize_negative(df['每万老人机构数（个/万人）'])

# 定义权重场景，波动≤±2%
weight_scenarios = {
    '原始逻辑（基准）': [0.35, 0.30, 0.25, 0.10],
    '场景1（小幅强化刚需）': [0.37, 0.30, 0.24, 0.09],
    '场景2（小幅强化供给）': [0.34, 0.32, 0.25, 0.09],
    '场景3（小幅强化规模）': [0.34, 0.29, 0.27, 0.10],
    '场景4（刚需+供给双强化）': [0.36, 0.31, 0.24, 0.09],
    '场景5（全指标小幅波动）': [0.33, 0.31, 0.26, 0.10]
}

# 计算各场景得分与排名
scenario_results = {}
for name, weights in weight_scenarios.items():
    df[f'{name}_得分'] = (
            df['失能占比标准化得分'] * weights[0] +
            df['机构数标准化得分'] * weights[1] +
            df['老年人口标准化得分'] * weights[2] +
            df['一人户标准化得分'] * weights[3]
    ).round(2)

    df_ranked = df.sort_values(f'{name}_得分', ascending=False).reset_index(drop=True)
    df_ranked[f'{name}_排名'] = df_ranked.index + 1

    scenario_results[name] = df_ranked[['地区', f'{name}_得分', f'{name}_排名']].copy()

# 合并所有场景结果，计算排名波动
final_result = scenario_results['原始逻辑（基准）'].rename(columns={
    '原始逻辑（基准）_得分': '基准得分', '原始逻辑（基准）_排名': '基准排名'
})
for name in weight_scenarios.keys():
    if name != '原始逻辑（基准）':
        final_result = final_result.merge(
            scenario_results[name][['地区', f'{name}_得分', f'{name}_排名']],
            on='地区', how='left'
        )


# 计算最大排名波动（核心稳定性指标）
def rank_fluctuation(row):
    ranks = [row['基准排名'],
             row['场景1（小幅强化刚需）_排名'], row['场景2（小幅强化供给）_排名'],
             row['场景3（小幅强化规模）_排名'], row['场景4（刚需+供给双强化）_排名'],
             row['场景5（全指标小幅波动）_排名']]
    return max(ranks) - min(ranks)


final_result['最大排名波动'] = final_result.apply(rank_fluctuation, axis=1)

# 保存结果
save_path = 'E:/Project/PythonProject1/权重敏感性测试_温和场景版.xlsx'
final_result.to_excel(save_path, index=False, engine='openpyxl')
