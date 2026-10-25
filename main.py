import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# 1. 读取原始CSV
df_household = pd.read_csv("各地区有65岁及以上老年人口的家庭户户数.csv", encoding='gbk')
df_health = pd.read_csv("各省老年人人数及健康情况.csv", encoding='gbk')
df_resource = pd.read_csv("各省养老资源.csv", encoding='gbk')
df_marriage = pd.read_csv("全国分性别、婚姻状况、健康状况的60岁及以上老年人口.csv", encoding='gbk')


# 2. 数据清洗
def clean_data():
    # 计算单身户占比
    df_household_clean = df_household.copy()
    df_household_clean["单身户占比(%)"] = (
            df_household_clean["单身老人户"] / df_household_clean["合计"] * 100
    ).round(2)

    # 计算不能自理相关指标
    df_health_clean = df_health.copy()
    df_health_clean["不能自理总人数"] = df_health_clean["生活不能自理男"] + df_health_clean["生活不能自理女"]
    df_health_clean["不能自理占比(%)"] = (
            df_health_clean["不能自理总人数"] / df_health_clean["60岁及以上合计"] * 100
    ).round(2)

    # 计算每万老人机构数（关键：用“养老机构”字段，和你的CSV匹配）
    df_resource_clean = df_resource.copy()
    df_health_region = df_health_clean[["地区", "60岁及以上合计"]].set_index("地区")
    df_resource_region = df_resource_clean.set_index("地区")
    df_merged_resource = pd.merge(df_resource_region, df_health_region, left_index=True, right_index=True, how="inner")
    df_merged_resource["每万老人机构数"] = (df_merged_resource["养老机构"] / df_merged_resource["60岁及以上合计"]) * 10000
    df_resource_clean = df_merged_resource.reset_index()

    # 计不能自理总人数
    df_marriage_clean = df_marriage.copy()
    df_marriage_clean["健康总人数"] = df_marriage_clean["健康男"] + df_marriage_clean["健康女"]
    # 不能自理总人数=生活不能自理男 + 生活不能自理女
    df_marriage_clean["不能自理总人数"] = df_marriage_clean["生活不能自理男"] + df_marriage_clean["生活不能自理女"]

    return df_household_clean, df_health_clean, df_resource_clean, df_marriage_clean


# 执行清洗
df_household_clean, df_health_clean, df_resource_clean, df_marriage_clean = clean_data()

# 3. SQL入库
def sql_store():
    try:
        engine = create_engine("sqlite:///elderly_care.db")
        create_table_sql = """
        -- 老年家庭户表（英文字段名）
        CREATE TABLE IF NOT EXISTS elderly_household (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL UNIQUE,  -- 地区
            total_household FLOAT,        -- 家庭户总数
            single_elderly_household FLOAT,  -- 单身老人户
            single_household_ratio REAL   -- 单身户占比（%）
        );

        -- 各省老年健康表（英文字段名）
        CREATE TABLE IF NOT EXISTS elderly_health_prov (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL UNIQUE,  -- 地区
            age_60_plus_total FLOAT,      -- 60岁及以上人口总数
            unable_self_care_male FLOAT,  -- 生活不能自理男
            unable_self_care_female FLOAT,-- 生活不能自理女
            unable_self_care_total FLOAT, -- 不能自理总人数
            unable_self_care_ratio REAL   -- 不能自理占比（%）
        );

        -- 各省养老资源表（英文字段名）
        CREATE TABLE IF NOT EXISTS elderly_resource_prov (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL UNIQUE,  -- 地区
            elderly_institution FLOAT,    -- 养老机构数
            elderly_meal_point FLOAT,     -- 老年助餐点数
            institution_per_10k FLOAT     -- 每万老人机构数
        );

        -- 老年健康婚姻表（英文字段名）
        CREATE TABLE IF NOT EXISTS elderly_health_marriage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marriage_status TEXT NOT NULL UNIQUE,  -- 婚姻状况
            age_60_plus_total FLOAT,               -- 60岁及以上人口总数
            unable_self_care_male FLOAT,           -- 生活不能自理男
            unable_self_care_female FLOAT,         -- 生活不能自理女
            healthy_total FLOAT                    -- 健康总人数
        );
        """

        with engine.connect() as conn:
            for sql_segment in create_table_sql.split(';'):
                sql_segment = sql_segment.strip()
                if sql_segment:
                    conn.execute(text(sql_segment))

            # 1. 家庭户表映射入库
            df_household_clean.rename(columns={
                "地区": "region",
                "合计": "total_household",
                "单身老人户": "single_elderly_household",
                "单身户占比(%)": "single_household_ratio"
            })[["region", "total_household", "single_elderly_household", "single_household_ratio"]].to_sql(
                "elderly_household", engine, if_exists="replace", index=False
            )

            # 2. 健康表映射入库
            df_health_clean.rename(columns={
                "地区": "region",
                "60岁及以上合计": "age_60_plus_total",
                "生活不能自理男": "unable_self_care_male",
                "生活不能自理女": "unable_self_care_female",
                "不能自理总人数": "unable_self_care_total",
                "不能自理占比(%)": "unable_self_care_ratio"
            })[["region", "age_60_plus_total", "unable_self_care_male", "unable_self_care_female",
                "unable_self_care_total", "unable_self_care_ratio"]].to_sql(
                "elderly_health_prov", engine, if_exists="replace", index=False
            )

            # 3. 资源表映射入库
            df_resource_clean.rename(columns={
                "地区": "region",
                "养老机构": "elderly_institution",
                "老年助餐点": "elderly_meal_point",
                "每万老人机构数": "institution_per_10k"
            })[["region", "elderly_institution", "elderly_meal_point", "institution_per_10k"]].to_sql(
                "elderly_resource_prov", engine, if_exists="replace", index=False
            )

            # 4. 婚姻表映射入库
            df_marriage_clean.rename(columns={
                "婚姻状况": "marriage_status",
                "60岁及以上合计": "age_60_plus_total",
                "生活不能自理男": "unable_self_care_male",
                "生活不能自理女": "unable_self_care_female",
                "健康总人数": "healthy_total"
            })[["marriage_status", "age_60_plus_total", "unable_self_care_male",
                "unable_self_care_female", "healthy_total"]].to_sql(
                "elderly_health_marriage", engine, if_exists="replace", index=False
            )

            conn.commit()
        return engine

    except Exception as e:
        print(f"\n❌ SQL入库失败：{str(e)}")
        exit()

engine = sql_store()

# 4. 分析+可视化（最终修改：SQL别名用纯中文）
def analysis_and_viz(engine):
    # 1.分析：资源缺口TOP5省份
    query = """
    SELECT 
        h.region AS 地区,  -- 纯中文，无特殊符号
        h.single_household_ratio AS 单身户占比,  -- 去掉%，纯中文
        ROUND(hp.unable_self_care_ratio, 2) AS 不能自理占比,  -- 去掉%，纯中文
        ROUND(r.institution_per_10k, 2) AS 每万老人机构数  -- 纯中文，无特殊符号
    FROM elderly_household h
    JOIN elderly_health_prov hp ON h.region = hp.region
    JOIN elderly_resource_prov r ON h.region = r.region
    ORDER BY r.institution_per_10k ASC  -- 按资源缺口升序（数值越少，缺口越大）
    LIMIT 5;
    """


    # 可视化1：各省单身老人户占比TOP10
    plt.figure(figsize=(12, 6))
    top10_single = df_household_clean.nlargest(10, "单身户占比(%)")  # DataFrame字段名可保留%
    plt.bar(top10_single["地区"], top10_single["单身户占比(%)"], color="#FF6B6B")
    plt.title("各省65岁及以上老年人口单身家庭户占比TOP10", fontsize=14)
    plt.xlabel("地区", fontsize=12)
    plt.ylabel("单身家庭户占比（%）", fontsize=12)  # 图表标签可保留%
    plt.xticks(rotation=45)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("single_household_top10.png", dpi=300)

    # 可视化2：全国老年婚姻与健康关联
    plt.figure(figsize=(12, 7))
    # 关键修改：用copy()明确创建独立DataFrame，避免视图/副本歧义
    marriage_health = df_marriage_clean[["婚姻状况", "健康总人数", "不能自理总人数"]].copy()
    # 新增列（此时操作的是独立副本，无警告）
    marriage_health["健康总人数(万)"] = marriage_health["健康总人数"] / 10000
    marriage_health["不能自理总人数(万)"] = marriage_health["不能自理总人数"] / 10000
    ax = marriage_health.set_index("婚姻状况")[["健康总人数(万)", "不能自理总人数(万)"]].plot(
        kind="bar", color=["#4ECDC4", "#FF6B6B"], width=0.6
    )
    plt.title("全国60岁及以上老年人口婚姻状况与健康状况关联", fontsize=16, pad=20)
    plt.xlabel("婚姻状况", fontsize=14)
    plt.ylabel("人数（万人）", fontsize=14)
    plt.xticks(rotation=0, fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(title="健康状况", labels=["健康人数", "不能自理人数"], fontsize=12)
    plt.grid(axis="y", alpha=0.3, linestyle="--")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", fontsize=10, padding=3)

    plt.tight_layout()
    plt.savefig("marriage_health_relation_optimized.png", dpi=300)


    # 可视化3 全国各省60岁及以上老年人口总数柱状图
    def plot_elderly_population_by_province(df_health_clean):
        df_prov = df_health_clean[~df_health_clean["地区"].isin(["全国", "总计"])].copy()
        df_prov_sorted = df_prov.sort_values("60岁及以上合计", ascending=True)
        plt.figure(figsize=(14, 10))
        bars = plt.barh(
            df_prov_sorted["地区"],
            df_prov_sorted["60岁及以上合计"] / 10000,
            color="#2E86AB",
            alpha=0.8
        )
        plt.title("全国各省60岁及以上老年人口总数（单位：万人）", fontsize=16, pad=20)
        plt.xlabel("老年人口数（万人）", fontsize=14)
        plt.ylabel("省份", fontsize=14)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=11)
        plt.grid(axis="x", alpha=0.3, linestyle="--")

        # 数值标签
        for bar in bars:
            width = bar.get_width()
            plt.text(
                width + 5,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.0f}",
                va="center",
                fontsize=9
            )
        plt.tight_layout()
        plt.savefig("elderly_population_by_province.png", dpi=300, bbox_inches="tight")

    plot_elderly_population_by_province(df_health_clean)


    # 可视化4 全国各省老年人不能自理占比柱状图
    def plot_unable_self_care_ratio(df_health_clean):
        df_prov = df_health_clean[~df_health_clean["地区"].isin(["全国", "总计"])].copy()
        df_prov["不能自理总人数"] = df_prov["生活不能自理男"] + df_prov["生活不能自理女"]
        df_prov["不能自理占比(%)"] = (df_prov["不能自理总人数"] / df_prov["60岁及以上合计"]) * 100
        df_prov_sorted = df_prov.sort_values("不能自理占比(%)", ascending=True)
        plt.figure(figsize=(14, 10))
        bars = plt.barh(
            df_prov_sorted["地区"],
            df_prov_sorted["不能自理占比(%)"],
            color="#E74C3C",
            alpha=0.8
        )
        plt.title("全国各省60岁及以上老年人不能自理占比（单位：%）", fontsize=16, pad=20)
        plt.xlabel("不能自理占比（%）", fontsize=14)
        plt.ylabel("省份", fontsize=14)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=11)
        plt.grid(axis="x", alpha=0.3, linestyle="--")
        for bar in bars:
            width = bar.get_width()
            plt.text(
                width + 0.05,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.2f}",
                va="center",
                fontsize=9
            )

        plt.tight_layout()
        plt.savefig("unable_self_care_ratio_by_province.png", dpi=300, bbox_inches="tight")

    plot_unable_self_care_ratio(df_health_clean)

    # 可视化5 全国各省每万老人机构数柱状图
    def plot_institution_per_10k_elderly(df_health_clean, df_resource_clean):
        df_prov = df_resource_clean[~df_resource_clean["地区"].isin(["全国", "总计"])].copy()
        df_prov_sorted = df_prov.sort_values("每万老人机构数", ascending=True)
        plt.figure(figsize=(14, 10))
        bars = plt.barh(
            df_prov_sorted["地区"],
            df_prov_sorted["每万老人机构数"],
            color="#3498DB",
            alpha=0.8
        )
        plt.title("全国各省每万60岁及以上老人拥有养老机构数", fontsize=16, pad=20)
        plt.xlabel("每万老人机构数（个/万人）", fontsize=14)
        plt.ylabel("省份", fontsize=14)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=11)
        plt.grid(axis="x", alpha=0.3, linestyle="--")
        for bar in bars:
            width = bar.get_width()
            plt.text(
                width + 0.1,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.2f}",
                va="center",
                fontsize=9
            )

        plt.tight_layout()
        plt.savefig("institution_per_10k_elderly.png", dpi=300, bbox_inches="tight")

    plot_institution_per_10k_elderly(df_health_clean, df_resource_clean)



analysis_and_viz(engine)