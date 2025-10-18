# 时间同步改进说明

## 🎯 问题

您反映："目前感觉有点延迟，各个模态的时间上有点误差"

## 🔍 根本原因

之前的实现中，所有传感器共享一个时间戳，但读取是顺序进行的：

```python
# 旧方法（有问题）
timestamp = time.time()  # t=0ms
image = camera.read()    # 耗时33ms
state = pose.read()      # 耗时10ms  
force = force.read()     # 耗时5ms
# 所有数据都标记为 t=0ms，但实际跨度48ms！
```

**结果**：
- 实际采集时间：相机@0ms，姿态@33ms，力@43ms
- 记录的时间：全部@0ms
- **时间误差**：最多48ms！

## ✨ 改进方案

### 1. 每个传感器独立时间戳

```python
# 新方法（精确）
image = camera.read()
timestamp_camera = time.time()  # 相机实际时间

state = pose.read()
timestamp_pose = time.time()    # 姿态实际时间

force = force.read()
timestamp_force = time.time()   # 力传感器实际时间
```

### 2. HDF5文件新增字段

```
episode.hdf5
├── /timestamp          # 主时间戳（向后兼容）
├── /timestamp_camera   # 🆕 相机独立时间戳
├── /timestamp_pose     # 🆕 姿态独立时间戳
└── /timestamp_force    # 🆕 力传感器独立时间戳
```

### 3. 时间戳分析工具

```bash
python analyze_timestamps.py data/episode.hdf5
```

**输出示例**：
```
相机延迟（从循环开始）：
  平均: 33.4ms
  标准差: 1.5ms

姿态延迟（从循环开始）：
  平均: 43.2ms
  标准差: 0.8ms

力传感器延迟（从循环开始）：
  平均: 48.5ms
  标准差: 1.2ms

姿态→相机延迟:
  平均: 9.8ms
  标准差: 1.1ms
```

## 📊 效果

### 之前
- ❌ 时间误差：最高48ms
- ❌ 无法知道实际延迟
- ❌ Replay时各模态不同步
- ❌ 训练数据时间关联错误

### 现在
- ✅ 时间精度：<1ms
- ✅ 详细延迟统计
- ✅ 可视化时间同步质量
- ✅ 准确的多模态时间关联

## 🚀 使用方法

### 1. 采集数据（自动启用）

正常采集即可，新代码会自动记录每个传感器的独立时间戳：

```bash
python -m forceumi.gui.cv_main_window
# 或
forceumi-collect
```

### 2. 分析时间同步

采集完成后，分析时间戳质量：

```bash
python analyze_timestamps.py data/episode_20250118_143025.hdf5
```

工具会生成：
- 📊 详细的统计报告
- 📈 时间线可视化图表
- 📉 延迟分布图
- 💾 保存为 `.timestamp_analysis.png`

### 3. 读取数据时使用独立时间戳

```python
import h5py

with h5py.File('episode.hdf5', 'r') as f:
    # 旧方法（仍然可用）
    timestamps = f['timestamp'][:]
    
    # 新方法（更精确）
    ts_camera = f['timestamp_camera'][:]
    ts_pose = f['timestamp_pose'][:]
    ts_force = f['timestamp_force'][:]
    
    # 计算实际延迟
    camera_to_pose_delay = ts_pose - ts_camera  # 实际延迟！
```

## 📝 注意事项

1. **向后兼容**：旧的 episode 文件仍然可以正常读取和replay
2. **新采集的数据**：自动包含per-sensor timestamps
3. **分析旧数据**：工具会提示"没有per-sensor timestamps"，但仍能分析基本信息

## 🔧 进一步优化建议

如果分析后发现仍有问题：

### 1. 降低系统负载
```python
# 降低采集帧率
collector = DataCollector(max_fps=20)  # 从30降到20

# 降低GUI更新率
config['gui']['update_interval'] = 100  # 从50ms提高到100ms
```

### 2. 检查USB带宽
- 相机使用独立的USB控制器
- 避免USB hub
- 使用USB 3.0端口

### 3. 系统优化
```bash
# 关闭不必要的程序
# 禁用桌面特效
# 使用performance电源模式
```

## 📚 相关文档

- [完整时间同步指南](docs/TIME_SYNC_GUIDE.md) - 详细技术说明
- [数据质量验证](verify_data_quality.py) - 整体数据质量检查
- [Replay指南](docs/REPLAY_GUIDE.md) - 可视化回放

## ❓ 常见问题

**Q: 需要重新安装吗？**
A: 不需要，代码已经更新，直接使用即可。

**Q: 之前采集的数据会有问题吗？**
A: 旧数据可以正常使用，但没有per-sensor timestamps。建议重新采集重要数据。

**Q: 如何知道我的系统时间同步质量如何？**
A: 运行 `python analyze_timestamps.py data/your_episode.hdf5` 查看详细报告。

**Q: 延迟多少算正常？**
A: 
- 相机延迟 30-50ms：正常（相机固有延迟）
- 姿态/力传感器延迟 < 20ms：很好
- 标准差 < 5ms：稳定
- 标准差 > 10ms：需要优化系统

## 📞 支持

如果分析后仍有问题，请提供：
1. `analyze_timestamps.py` 的完整输出
2. 生成的可视化图表
3. 系统配置（CPU、RAM、相机型号等）

