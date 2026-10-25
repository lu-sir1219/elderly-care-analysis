# 全国老年人口需求与养老资源匹配分析

基于多维度公开数据的养老需求分析项目：对全国各省 60 岁及以上老年人口的家庭结构、健康状况、婚姻状况与养老资源（养老机构、助餐点）进行清洗、入库、可视化和聚类分析，输出各省养老需求优先级排名与资源缺口判断。

## 数据来源

| 数据 | 说明 |
|---|---|
| 各地区有 65 岁及以上老年人口的家庭户户数 | 单身老人户、家庭户总数（全国人口普查） |
| 各省老年人人数及健康情况 | 60 岁及以上人口、生活不能自理（男/女） |
| 各省养老资源 | 养老机构数、老年助餐点数 |
| 全国分性别、婚姻状况、健康状况的 60 岁及以上老年人口 | 婚姻状况 × 健康/不能自理交叉数据 |
| 全国各地区一人户统计 / 一人户原表 | 独居老人补充数据 |

## 分析流程

```
原始 CSV（gbk 编码）
   │  pandas 清洗（计算单身户占比 / 不能自理占比 / 每万老人机构数）
   ▼
SQLite 入库（4 张表：household / health / resource / marriage）
   │  SQL 关联查询（如：资源缺口 TOP5 省份）
   ▼
可视化（matplotlib，5 类柱状图/条形图）
   │
   ▼
聚类分析（K-means：失能占比 × 独居占比，肘部法则选 K）
   │
   ▼
指标排名 + 权重敏感性测试 → 各省养老需求优先级排名
```

## 目录结构

```
.
├── main.py                      # 主流程：清洗 → SQLite 入库 → 5 类可视化 → 资源缺口 TOP5
├── k-means（失能占比-独居）.py       # K-means 聚类（失能占比 × 独居占比）
├── 失能-万老人机构.py              # 每万老人机构数指标计算
├── 养老指标排名.py                 # 各省养老需求优先级排名
├── 敏感性测试.py                  # 权重敏感性测试
├── 深度分析.py                    # 补充深度分析
├── elderly_care.db / 养老分析.db   # SQLite 数据库
├── *.xlsx / *.csv               # 原始数据 + 结果表
├── *.png                        # 可视化输出
└── 基于多维度数据的老年人群需求与养老资源匹配分析报告.docx   # 完整报告
```

## 关键可视化

- `single_household_top10.png` —— 各省 65 岁及以上老年单身家庭户占比 TOP10
- `elderly_population_by_province.png` —— 各省 60 岁及以上老年人口总数
- `unable_self_care_ratio_by_province.png` —— 各省不能自理老人占比
- `institution_per_10k_elderly.png` —— 各省每万老人拥有养老机构数
- `marriage_health_relation_optimized.png` —— 婚姻状况与健康状况关联
- `独居-失能需求象限图.png` / `Disabled-Institution_Kmeans_Cluster.png` —— 聚类与象限图

## 复现方法

```bash
pip install -r requirements.txt
python main.py
```

> 注意：代码用 `plt.rcParams['font.sans-serif'] = ['SimHei']` 显示中文，Linux/macOS 需先安装中文字体或改用系统可用字体。

## 许可

课程/调研分析项目，仅供学习与面试展示。
