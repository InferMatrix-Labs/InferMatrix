# -*- coding: utf-8 -*-
#字体设置
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def read_and_process_excel(file_path):
    """读取Excel文件并提取指定行数据"""
    # 读取Excel文件
    df = pd.read_excel(file_path, header=2)
    print(f"数据总行数: {len(df)}")
    #print(df.head())
    #print(df.dtypes)  # 打印每列类型
    # 提取指定的行
    rows = {}
    for i in range(min(7, len(df))):
        rows[f"row{i+1}"] = df.iloc[i].to_dict()

    # 提取所有列名
    columns = list(df.columns)
    
    # 过滤非数值类型的列（保留数值类型的数据）
    numeric_columns = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]
    print("完整DataFrame：")
    print(df)
    #print("rows内容：")
    #for k, v in rows.items():
    #    print(k, v)
    print("numeric_columns:", numeric_columns)
    return rows, numeric_columns

def plot_comparison_chart(data_sets, columns, chart_title, save_path):
    """绘制对比图表并保存"""
    plt.figure(figsize=(15, 8))
    
    # 设置颜色方案
    colors = plt.cm.tab10(np.linspace(0, 1, len(data_sets)))
    
    # 计算柱状图位置
    bar_width = 0.2
    positions = np.arange(len(columns))
    
    # 绘制每组数据的柱状图
    for idx, (label, data) in enumerate(data_sets.items()):
        values = [data.get(col, 0) for col in columns]
        plt.bar(positions + idx * bar_width, values, width=bar_width, 
                label=label, color=colors[idx])
    
    # 添加数据标签
    for label, data in data_sets.items():
        values = [data.get(col, 0) for col in columns]
        for pos, value in enumerate(values):
            plt.text(positions[pos] + list(data_sets.keys()).index(label) * bar_width, 
                     value + max(values)/50, f'{value:.2f}', 
                     ha='center', va='bottom', fontsize=9, rotation=90)
    
    # 设置图表标题和标签
    plt.title(f'{chart_title} 对比分析', fontsize=16, fontweight='bold')
    plt.ylabel('数值', fontsize=12)
    plt.xlabel('指标', fontsize=12)
    
    # 设置X轴刻度和标签
    plt.xticks(positions + bar_width * (len(data_sets)-1)/2, 
               columns, fontsize=10, rotation=45, ha='right')
    
    # 添加网格线和图例
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(loc='best', fontsize=10, frameon=True, shadow=True)
    
    # 调整布局和保存
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"图表已保存至: {save_path}")

def main():
    # 文件路径设置
    excel_file = 'config不同参数测试结果.xls'  # 替换为实际文件名
    output_dir = 'pictures'
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取和处理Excel数据
    try:
        rows, numeric_columns = read_and_process_excel(excel_file)
        print(f"成功读取文件: {excel_file}")
        #print(f"包含数值列: {numeric_columns}")
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return
    #舍去参数
    numeric_columns=numeric_columns[3:]
    # TTFT对比
    chart1_data = {
        "第一组数据": rows['row1'],
        "第二组数据": rows['row2'],
        "第三组数据": rows['row3']
    }
    plot_comparison_chart(
        chart1_data, 
        numeric_columns[0:4],
        "第一、二、三组数据",
        os.path.join(output_dir, 'TTFT对比图.png')
    )
    # TPOT对比
    chart1_data = {
        "第一组数据": rows['row1'],
        "第二组数据": rows['row2'],
        "第三组数据": rows['row3']
    }
    plot_comparison_chart(
        chart1_data, 
        numeric_columns[4:8],
        "第一、二、三组数据",
        os.path.join(output_dir, 'TPOT对比图.png')
    )
    # Throughput对比
    chart1_data = {
        "第一组数据": rows['row1'],
        "第二组数据": rows['row2'],
        "第三组数据": rows['row3']
    }
    plot_comparison_chart(
        chart1_data, 
        numeric_columns[8:12],
        "第一、二、三组数据",
        os.path.join(output_dir, 'Throughput对比图.png')
    )
    # tokens和total time对比
    chart1_data = {
        "第一组数据": rows['row1'],
        "第二组数据": rows['row2'],
        "第三组数据": rows['row3']
    }
    plot_comparison_chart(
        chart1_data, 
        numeric_columns[12:16],
        "第一、二、三组数据",
        os.path.join(output_dir, 'tokens和total time对比图.png')
    )

    print("\n所有图表生成完成！")

if __name__ == "__main__":
    main()
