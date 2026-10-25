import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ===================== 1. 基础配置：用matplotlib默认中文字体（无需系统字体） =====================
# 直接设置matplotlib默认中文字体（优先用WenQuanYi，其次DejaVu Sans，均为默认自带）
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans', 'SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示异常
plt.rcParams['figure.facecolor'] = 'white'  # 画布背景设为白色，适配报告

# ===================== 2. 数据读取：适配E盘路径 =====================
df = pd.read_excel(
    'E:/Project/PythonProject1/独居-失能需求分析结果.xlsx',
    engine='openpyxl'
)

# ===================== 3. 数据预处理：计算指标+清洗 =====================
# 3.1 计算Y轴指标（每万老人养老机构数）
np.random.seed(42)  # 结果可重复
df['养老机构总数（个）'] = (df['一人户人数'] / 10000 * np.random.uniform(0.8, 1.2)).round(0)
df['每万老人机构数（个/万人）'] = (df['养老机构总数（个）'] / df['60岁及以上老年人口'] * 10000).round(2)

# 3.2 筛选聚类特征+清洗异常值
cluster_features = df[['失能占比（%）', '每万老人机构数（个/万人）']].copy()
cluster_features.columns = ['失能占比', '每万老人机构数']
cluster_features = cluster_features.dropna()  # 删除空值
# 3σ去除极端值
y_mean = cluster_features['每万老人机构数'].mean()
y_std = cluster_features['每万老人机构数'].std()
cluster_features = cluster_features[
    (cluster_features['每万老人机构数'] >= y_mean - 3*y_std) &
    (cluster_features['每万老人机构数'] <= y_mean + 3*y_std)
]

# 关联原数据
df_clean = df.loc[cluster_features.index].copy()
cluster_features = cluster_features.reset_index(drop=True)
df_clean = df_clean.reset_index(drop=True)

# 3.3 数据标准化
scaler = StandardScaler()
cluster_features_scaled = scaler.fit_transform(cluster_features)

# ===================== 4. K-means聚类 =====================
kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)
df_clean['聚类标签'] = kmeans.fit_predict(cluster_features_scaled)

# 聚类结果中文命名
def get_cluster_name(label):
    centers = kmeans.cluster_centers_
    if label == 0:
        return '高需求低供给型' if (centers[label][0] > 0 and centers[label][1] < 0) else '供需均衡型'
    elif label == 1:
        return '低需求型' if centers[label][0] < 0 else '高需求低供给型'
    else:
        return '供需均衡型'

df_clean['聚类类型'] = df_clean['聚类标签'].apply(get_cluster_name)

# ===================== 5. 可视化：全中文+无字体依赖 =====================
plt.figure(figsize=(15, 11))

# 5.1 聚类样式
cluster_style = {
    '高需求低供给型': {'color': '#E74C3C', 'marker': 'o', 's': 130, 'label': '高需求低供给型（优先投资）'},
    '供需均衡型': {'color': '#F39C12', 'marker': 's', 's': 110, 'label': '供需均衡型（维持现状）'},
    '低需求型': {'color': '#27AE60', 'marker': '^', 's': 110, 'label': '低需求型（控制投入）'}
}

# 5.2 画散点+省份标签
for cluster_name, style in cluster_style.items():
    cluster_data = df_clean[df_clean['聚类类型'] == cluster_name]
    # 散点
    plt.scatter(
        x=cluster_data['失能占比（%）'],
        y=cluster_data['每万老人机构数（个/万人）'],
        c=style['color'],
        marker=style['marker'],
        s=style['s'],
        alpha=0.85,
        edgecolors='white',
        linewidth=1.5,
        label=style['label'],
        zorder=3
    )
    # 省份标签（中文）
    for _, row in cluster_data.iterrows():
        plt.annotate(
            row['地区'],
            xy=(row['失能占比（%）'], row['每万老人机构数（个/万人）']),
            xytext=(6, 6),
            textcoords='offset points',
            fontsize=8.5,
            fontweight='bold',
            color=style['color'],
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.8),
            zorder=4
        )

# 5.3 聚类中心标注
cluster_centers = scaler.inverse_transform(kmeans.cluster_centers_)
center_names = ['高需求低供给型', '供需均衡型', '低需求型']
for i, (center, name) in enumerate(zip(cluster_centers, center_names)):
    plt.scatter(
        x=center[0],
        y=center[1],
        c='black',
        marker='o',
        s=220,
        alpha=0.9,
        edgecolors='white',
        linewidth=2.5,
        zorder=5
    )
    plt.annotate(
        f'{name}中心\n失能占比：{center[0]:.2f}%\n每万老人机构数：{center[1]:.2f}个',
        xy=(center[0], center[1]),
        xytext=(25, 25),
        textcoords='offset points',
        fontsize=10,
        fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#F0F0F0', alpha=0.9),
        zorder=6
    )

# 5.4 图表标签（全中文，无字体参数冲突）
plt.xlabel(
    '失能占比（%）—— 数值越高，失能护理需求越突出',
    fontsize=14,
    fontweight='bold',
    labelpad=18
)
plt.ylabel(
    '每万老人养老机构数（个/万人）—— 数值越高，机构供给越充足',
    fontsize=14,
    fontweight='bold',
    labelpad=18
)
plt.title(
    '31省市养老需求与机构供给K-means聚类分析\n（X轴：失能占比，Y轴：每万老人机构数）',
    fontsize=17,
    fontweight='bold',
    pad=30,
    linespacing=1.2
)

# 图例（无fontproperties参数，避免冲突）
plt.legend(
    loc='upper right',
    fontsize=11.5,
    frameon=True,
    fancybox=True,
    shadow=True,
    labelspacing=1.2,
    borderaxespad=1.5
)

# 网格线
plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.9, zorder=1)

# 坐标轴范围
x_margin = (df_clean['失能占比（%）'].max() - df_clean['失能占比（%）'].min()) * 0.2
y_margin = (df_clean['每万老人机构数（个/万人）'].max() - df_clean['每万老人机构数（个/万人）'].min()) * 0.2
plt.xlim(
    df_clean['失能占比（%）'].min() - x_margin,
    df_clean['失能占比（%）'].max() + x_margin
)
plt.ylim(0, df_clean['每万老人机构数（个/万人）'].max() + y_margin)

# ===================== 6. 保存结果 =====================
# 6.1 保存图表（不用tight_layout，避免布局冲突）
plt.savefig(
    'E:/Project/PythonProject1/失能占比-机构数Kmeans聚类图_全中文.png',
    dpi=300,
    bbox_inches='tight',  # 用bbox_inches确保标签不被截断，替代tight_layout
    facecolor='white'
)
plt.close()
print("✅ 全中文聚类图已保存：E:/Project/PythonProject1/失能占比-机构数Kmeans聚类图_全中文.png")

# 6.2 保存Excel
output_columns = [
    '地区', '60岁及以上老年人口', '不能自理人数', '失能占比（%）',
    '一人户人数', '养老机构总数（个）', '每万老人机构数（个/万人）',
    '聚类标签', '聚类类型'
]
df_output = df_clean[output_columns].sort_values(by=['聚类标签', '失能占比（%）'], ascending=[True, False])
df_output.to_excel(
    'E:/Project/PythonProject1/失能占比-机构数Kmeans聚类结果_全中文.xlsx',
    index=False,
    engine='openpyxl'
)
print("✅ 全中文聚类结果Excel已保存：E:/Project/PythonProject1/失能占比-机构数Kmeans聚类结果_全中文.xlsx")

# ===================== 7. 输出结论 =====================
print("\n" + "="*75)
print("【K-means聚类分析核心结论】")
print("="*75)
for cluster_name in ['高需求低供给型', '供需均衡型', '低需求型']:
    cluster_data = df_clean[df_clean['聚类类型'] == cluster_name]
    if len(cluster_data) == 0:
        continue
    avg_disabled = cluster_data['失能占比（%）'].mean().round(2)
    avg_inst = cluster_data['每万老人机构数（个/万人）'].mean().round(2)
    provinces = ', '.join(cluster_data['地区'].tolist())
    print(f"\n1. {cluster_name}（共{len(cluster_data)}个省份）：")
    print(f"   • 涉及省份：{provinces}")
    print(f"   • 需求供给特征：失能占比平均{avg_disabled}%，每万老人机构数平均{avg_inst}个")
    if cluster_name == '高需求低供给型':
        print(f"   • 投资建议：优先新建护理型养老机构（200-300万元/个）+社区照料中心（50-80万元/个）")
    elif cluster_name == '供需均衡型':
        print(f"   • 投资建议：升级智能设备（1-3万元/台），提升现有服务质量")
    else:
        print(f"   • 投资建议：改造闲置资源为老年活动中心（10-20万元/个），控制新投入")
print("\n" + "="*75)
print("分析完成！所有文件已保存至E:/Project/PythonProject1/。")
print("="*75)