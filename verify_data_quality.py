#!/usr/bin/env python3
"""
验证采集数据的质量 - 检查时间戳是否均匀
"""

import numpy as np
import sys
from pathlib import Path
from forceumi.data import HDF5Manager


def analyze_episode(filepath):
    """分析episode的时间戳质量"""
    print(f"\n分析文件: {filepath}")
    print("=" * 60)
    
    # 加载数据
    manager = HDF5Manager()
    data = manager.load_episode(filepath)
    
    if data is None:
        print("❌ 无法加载数据")
        return
    
    timestamps = data['timestamp']
    num_frames = len(timestamps)
    
    # 计算时间间隔
    time_diffs = np.diff(timestamps)
    
    # 统计信息
    duration = timestamps[-1] - timestamps[0]
    actual_fps = num_frames / duration if duration > 0 else 0
    
    print(f"总帧数: {num_frames}")
    print(f"总时长: {duration:.3f} 秒")
    print(f"实际FPS: {actual_fps:.2f}")
    print()
    
    # 时间间隔统计
    print("时间间隔统计 (毫秒):")
    print(f"  平均: {np.mean(time_diffs) * 1000:.2f} ms")
    print(f"  标准差: {np.std(time_diffs) * 1000:.2f} ms")
    print(f"  最小: {np.min(time_diffs) * 1000:.2f} ms")
    print(f"  最大: {np.max(time_diffs) * 1000:.2f} ms")
    print(f"  中位数: {np.median(time_diffs) * 1000:.2f} ms")
    print()
    
    # 检查异常值
    mean_diff = np.mean(time_diffs)
    std_diff = np.std(time_diffs)
    outliers = np.abs(time_diffs - mean_diff) > 3 * std_diff
    num_outliers = np.sum(outliers)
    
    print(f"异常帧间隔 (>3σ): {num_outliers} / {len(time_diffs)} ({num_outliers/len(time_diffs)*100:.2f}%)")
    
    if num_outliers > 0:
        print(f"  最大偏差: {np.max(np.abs(time_diffs - mean_diff)) * 1000:.2f} ms")
        outlier_indices = np.where(outliers)[0]
        print(f"  异常位置 (前10个): {outlier_indices[:10]}")
    
    # 判断数据质量
    print()
    print("数据质量评估:")
    
    jitter = np.std(time_diffs) / np.mean(time_diffs) * 100
    print(f"  时间抖动: {jitter:.2f}%")
    
    if jitter < 5:
        print("  ✅ 优秀 - 时间戳非常均匀")
    elif jitter < 10:
        print("  ✅ 良好 - 时间戳较为均匀")
    elif jitter < 20:
        print("  ⚠️  一般 - 有一定抖动")
    else:
        print("  ❌ 较差 - 抖动明显")
    
    # 检查数据形状
    print()
    print("数据形状:")
    for key in ['image', 'state', 'action', 'force']:
        if key in data and data[key] is not None:
            print(f"  {key}: {data[key].shape}")
    
    return {
        'num_frames': num_frames,
        'duration': duration,
        'actual_fps': actual_fps,
        'mean_interval': np.mean(time_diffs),
        'jitter_percent': jitter,
        'num_outliers': num_outliers
    }


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python verify_data_quality.py <episode_file.hdf5>")
        print()
        print("或者分析最新的episode:")
        data_dir = Path("./data")
        if data_dir.exists():
            episodes = sorted(data_dir.glob("episode_*.hdf5"), key=lambda x: x.stat().st_mtime)
            if episodes:
                latest = episodes[-1]
                print(f"分析最新episode: {latest}")
                analyze_episode(str(latest))
            else:
                print("❌ data目录中没有找到episode文件")
        else:
            print("❌ data目录不存在")
        return
    
    filepath = sys.argv[1]
    analyze_episode(filepath)


if __name__ == "__main__":
    main()

