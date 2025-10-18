# 数据单位和约定

## 概述

本文档说明ForceUMI数据集中使用的单位和坐标系约定。

## 单位系统

### 位置（Position）

- **单位**：米 (meters)
- **坐标系**：右手坐标系
- **原点**：VR station (基站) 位置
- **轴定义**：
  - X: 前后方向
  - Y: 左右方向  
  - Z: 上下方向

### 姿态（Orientation）

- **表示方式**：Euler角 (roll, pitch, yaw)
- **单位**：弧度 (radians)
- **旋转顺序**：ZYX (yaw-pitch-roll)
- **范围**：[-π, π]

**⚠️ 重要提示**：
- PyTracker原始输出的角度为**度(degrees)**
- PoseSensor类会自动转换为**弧度(radians)**
- 最终数据集中的角度均为**弧度**

### 力/力矩（Force/Torque）

- **力 (fx, fy, fz)**：牛顿 (N)
- **力矩 (mx, my, mz)**：牛顿·米 (N·m)
- **坐标系**：传感器本地坐标系

### Gripper（夹爪）

- **单位**：无量纲 (0.0 到 1.0)
- **0.0**：完全闭合
- **1.0**：完全打开
- **类型**：绝对值（非增量）

### 时间戳（Timestamp）

- **单位**：秒 (seconds)
- **格式**：Unix时间戳 (float64)
- **精度**：微秒级

## 坐标系约定

### State坐标系

State数据表示tracker相对于VR station的绝对位姿：

```
        Z (up)
        |
        |
        |_________ Y (right)
       /
      /
     X (forward)
```

### Action坐标系

Action数据表示tracker相对于第一帧tracker位姿的相对变换：

```
第一帧tracker坐标系
        Z'
        |
        |
        |_________ Y'
       /
      /
     X'
```

## 角度转换

### PyTracker → ForceUMI 自动转换

```python
# PoseSensor内部自动执行
roll_degrees, pitch_degrees, yaw_degrees = pytracker.get_pose_euler()
roll_rad = np.deg2rad(roll_degrees)
pitch_rad = np.deg2rad(pitch_degrees)
yaw_rad = np.deg2rad(yaw_degrees)
```

### 用户手动转换（如需要）

```python
import numpy as np

# 度 -> 弧度
radians = np.deg2rad(degrees)

# 弧度 -> 度
degrees = np.rad2deg(radians)
```

## Euler角约定

### 旋转顺序：ZYX

1. **Yaw (ψ)**: 绕Z轴旋转
2. **Pitch (θ)**: 绕Y轴旋转
3. **Roll (φ)**: 绕X轴旋转

### 旋转矩阵

```
R = Rz(yaw) * Ry(pitch) * Rx(roll)
```

### 范围

- Roll: [-π, π]
- Pitch: [-π/2, π/2]
- Yaw: [-π, π]

## 数据类型

### HDF5存储类型

| 数据 | 形状 | 数据类型 | 单位 |
|------|------|----------|------|
| image | (N, H, W, 3) | uint8 | - |
| state | (N, 7) | float32 | [m, m, m, rad, rad, rad, -] |
| action | (N, 7) | float32 | [m, m, m, rad, rad, rad, -] |
| force | (N, 6) | float32 | [N, N, N, N·m, N·m, N·m] |
| timestamp | (N,) | float64 | seconds |

## 验证单位

### 检查角度单位

```python
import h5py
import numpy as np

with h5py.File("episode.hdf5", "r") as f:
    state = f["state"][:]
    
    # 检查角度范围（应该在 -π 到 π 之间）
    angles = state[:, 3:6]  # [rx, ry, rz]
    
    print(f"角度最小值: {angles.min():.3f} rad")
    print(f"角度最大值: {angles.max():.3f} rad")
    
    # 如果值远大于π，可能是度而不是弧度
    if np.abs(angles).max() > 10:
        print("⚠️ 警告：角度值似乎是度而不是弧度！")
    else:
        print("✅ 角度单位正确（弧度）")
```

### 检查位置单位

```python
# 检查位置范围（应该在合理的米范围内）
position = state[:, :3]  # [x, y, z]

print(f"位置范围: X[{position[:,0].min():.2f}, {position[:,0].max():.2f}]m")
print(f"          Y[{position[:,1].min():.2f}, {position[:,1].max():.2f}]m")
print(f"          Z[{position[:,2].min():.2f}, {position[:,2].max():.2f}]m")
```

## 常见错误

### ❌ 错误1：混淆度和弧度

```python
# 错误：直接使用PyTracker的度值
pose = tracker.get_pose_euler()
state = np.array([x, y, z, roll, pitch, yaw, gripper])  # 错误！角度是度

# 正确：使用PoseSensor类（自动转换）
state = pose_sensor.read()  # 正确！角度已转换为弧度
```

### ❌ 错误2：角度范围假设

```python
# 错误：假设角度在0到360度
if angle > 180:
    angle = angle - 360

# 正确：使用弧度范围[-π, π]
# numpy的np.arctan2等函数已返回正确范围
```

### ❌ 错误3：混淆旋转顺序

```python
# 错误：假设XYZ顺序
R = Rx(roll) * Ry(pitch) * Rz(yaw)

# 正确：使用ZYX顺序
R = Rz(yaw) * Ry(pitch) * Rx(roll)
# 或使用我们的工具函数
from forceumi.utils.transforms import euler_to_matrix
R = euler_to_matrix(roll, pitch, yaw)
```

## 参考文档

- 坐标转换工具：`forceumi/utils/transforms.py`
- PoseSensor实现：`forceumi/devices/pose_sensor.py`
- 数据格式说明：`README.md`
- Action坐标系：`ACTION_COORDINATE_SYSTEM.md`

## 版本历史

- **v0.3.0**: 添加自动度到弧度转换
- **v0.1.0**: 初始实现

