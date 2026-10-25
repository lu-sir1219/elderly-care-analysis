import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# 1. 基础配置
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'WenQuanYi Zen Hei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['figure.dpi'] = 100  # 适配屏幕显示

# 2. 读取单一表格
df = pd.read_excel(
    'E:/Project/PythonProject1/全国各省市老年人口状况调查.xlsx',  # 你的本地路径
    engine='openpyxl'
)

# 3. 数据预处理：计算指标+清洗
df['失能占比（%）'] = (df['不能自理人数'] / df['60岁及以上老年人口'] * 100).round(2)
df['独居占比（%）'] = (df['一人户人数'] / df['60岁及以上老年人口'] * 100).round(2)

df_clean = df[
    (df['60岁及以上老年人口'] > 0) &
    (df['失能占比（%）'].notna()) &
    (df['独居占比（%）'].notna())
    ].copy()

# 提取聚类特征（二维：失能占比、独居占比）
cluster_features = df_clean[['失能占比（%）', '独居占比（%）']].copy()
print(f"有效分析省份数量：{len(df_clean)}个（覆盖全国31省市）")
print(
    f"指标范围：失能占比{df_clean['失能占比（%）'].min():.2f}%-{df_clean['失能占比（%）'].max():.2f}%，独居占比{df_clean['独居占比（%）'].min():.2f}%-{df_clean['独居占比（%）'].max():.2f}%")

# 数据标准化（消除量级差异，确保聚类公平）
scaler = StandardScaler()
features_scaled = scaler.fit_transform(cluster_features)

#  执行K-means聚类
kmeans = KMeans(
    n_clusters=3,
    random_state=42,  # 固定随机种子
    n_init=10  # 多次初始化
)
df_clean['聚类标签'] = kmeans.fit_predict(features_scaled)

#  聚类标签业务化命名
cluster_stats = df_clean.groupby('聚类标签')[['失能占比（%）', '独居占比（%）']].mean().round(2)

# 定义标签
def get_cluster_name(label):
    avg_disabled = cluster_stats.loc[label, '失能占比（%）']
    avg_alone = cluster_stats.loc[label, '独居占比（%）']
    mean_disabled = df_clean['失能占比（%）'].mean()
    mean_alone = df_clean['独居占比（%）'].mean()

    if avg_disabled > mean_disabled and avg_alone > mean_alone:
        return '双高需求型'  # 失能高+独居高
    elif avg_disabled > mean_disabled and avg_alone <= mean_alone:
        return '失能主导型'  # 失能高+独居低
    else:
        return '基础需求型'  # 失能低（无论独居高低，归为基础需求）


df_clean['聚类类型'] = df_clean['聚类标签'].apply(get_cluster_name)

#  可视化：K-means聚类结果图）
plt.figure(figsize=(12, 8))

# 定义聚类样式
cluster_style = {
    '双高需求型': {'color': '#E74C3C', 'marker': 'o', 's': 120, 'label': '双高需求型（失能+独居均高）'},
    '失能主导型': {'color': '#3498DB', 'marker': 's', 's': 100, 'label': '失能主导型（失能高+独居低）'},
    '基础需求型': {'color': '#27AE60', 'marker': '^', 's': 100, 'label': '基础需求型（失能低）'}
}

for cluster_name, style in cluster_style.items():
    cluster_data = df_clean[df_clean['聚类类型'] == cluster_name]
    plt.scatter(
        x=cluster_data['失能占比（%）'],
        y=cluster_data['独居占比（%）'],
        c=style['color'],
        marker=style['marker'],
        s=style['s'],
        alpha=0.85,
        edgecolors='white',
        linewidth=1.5,
        label=style['label'],
        zorder=3
    )
    for _, row in cluster_data.iterrows():
        plt.annotate(
            row['地区'],
            xy=(row['失能占比（%）'], row['独居占比（%）']),
            xytext=(6, 6),
            textcoords='offset points',
            fontsize=8.5,
            fontweight='bold',
            color=style['color'],
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8),
            zorder=4
        )

# 绘制全国均值线
mean_disabled = df_clean['失能占比（%）'].mean()
mean_alone = df_clean['独居占比（%）'].mean()
plt.axvline(x=mean_disabled, color='#95A5A6', linestyle='--', linewidth=2, alpha=0.7,
            label=f'全国平均失能占比：{mean_disabled:.2f}%')
plt.axhline(y=mean_alone, color='#95A5A6', linestyle='--', linewidth=2, alpha=0.7,
            label=f'全国平均独居占比：{mean_alone:.2f}%')

# 标注聚类中心
cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
label_to_type = df_clean[['聚类标签', '聚类类型']].drop_duplicates().set_index('聚类标签')['聚类类型'].to_dict()

for label, center in enumerate(cluster_centers):
    cluster_name = label_to_type[label]
    plt.scatter(
        x=center[0],
        y=center[1],
        c='black',
        marker='o',
        s=200,
        alpha=0.9,
        edgecolors='white',
        linewidth=2,
        zorder=5
    )
    plt.annotate(
        f'{cluster_name}中心\n失能：{center[0]:.2f}%\n独居：{center[1]:.2f}%',
        xy=(center[0], center[1]),
        xytext=(15, 15),
        textcoords='offset points',
        fontsize=9,
        fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgray', alpha=0.9),
        zorder=6
    )

# 图表美化
plt.xlabel('失能占比（%）—— 数值越高，失能护理需求越突出', fontsize=12, fontweight='bold', labelpad=12)
plt.ylabel('独居占比（%）—— 数值越高，社区居家服务需求越突出', fontsize=12, fontweight='bold', labelpad=12)
plt.title('31省市养老需求K-means聚类分析（仅用老年人口调查数据）\n（X：失能占比，Y：独居占比）',
          fontsize=14, fontweight='bold', pad=20, linespacing=1.2)
plt.legend(loc='upper right', fontsize=10, frameon=True, fancybox=True, shadow=True)
plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.8, zorder=1)

# 保存结果（图表+表格，全中文）
plt.tight_layout()
plt.savefig('E:/Project/PythonProject1/养老需求Kmeans聚类图_单一表格版.png',
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

# 7.2 保存聚类结果表格
output_columns = [
    '地区', '60岁及以上老年人口', '不能自理人数', '失能占比（%）',
    '一人户人数', '独居占比（%）', '聚类标签', '聚类类型'
]
df_output = df_clean[output_columns].sort_values(by=['聚类标签', '失能占比（%）'], ascending=[True, False])
df_output.to_excel('E:/Project/PythonProject1/养老需求Kmeans聚类结果_单一表格版.xlsx',
                   index=False, engine='openpyxl'))

# 8. 核心结论
for cluster_name in cluster_style.keys():
    cluster_data = df_clean[df_clean['聚类类型'] == cluster_name]
    if len(cluster_data) == 0:
        continue
    avg_disabled = cluster_data['失能占比（%）'].mean().round(2)
    avg_alone = cluster_data['独居占比（%）'].mean().round(2)
    provinces = ', '.join(cluster_data['地区'].tolist())
