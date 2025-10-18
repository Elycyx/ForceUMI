# Action坐标系说明

## 概述

从版本 0.3.0 开始，**action** 数据的定义发生了重要变化：

- **之前**：action = state（tracker相对于station的绝对位姿）
- **现在**：action = tracker相对于第一帧tracker位姿的相对位姿

## 动机

这种变化使得action数据更适合：
1. **相对运动学习**：学习从起始位姿到目标位姿的相对运动
2. **任务泛化**：不同起始位置的任务可以共享相同的相对运动模式
3. **轨迹表示**：更直观地表示机械臂的运动轨迹

## 数据定义

### State（状态）- 绝对位姿

```python
state = [x, y, z, rx, ry, rz, gripper]
```

- **坐标系**：相对于VR station（基站）
- **含义**：tracker在世界坐标系中的绝对位姿
- **单位**：
  - 位置 (x,y,z)：米
  - 姿态 (rx,ry,rz)：弧度（Euler角）
  - gripper：0.0-1.0（绝对值）

### Action（动作）- 相对位姿

```python
action = [x, y, z, rx, ry, rz, gripper]
```

- **坐标系**：相对于第一帧的tracker位姿
- **含义**：当前帧相对于第一帧的位姿变换
- **特性**：
  - **第一帧**：`action = [0, 0, 0, 0, 0, 0, gripper_0]`
  - **后续帧**：表示相对于第一帧的位姿变化
  - gripper：始终为绝对值（与state相同）

## 实现细节

### 坐标转换

使用齐次变换矩阵计算相对位姿：

```python
from forceumi.utils.transforms import relative_pose

# 第一帧（参考帧）
reference_pose = [1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.5]

# 当前帧
current_pose = [1.1, 2.2, 3.0, 0.0, 0.0, 0.1, 0.7]

# 计算相对位姿
action = relative_pose(current_pose, reference_pose)
# action表示从reference_pose到current_pose的变换
```

### 转换流程

1. 将6D pose转换为4x4齐次变换矩阵
2. 计算相对变换：`T_relative = T_ref^(-1) * T_current`
3. 将变换矩阵转换回6D pose
4. 保留原始gripper值

## 使用示例

### 读取数据

```python
from forceumi.data import HDF5Manager

manager = HDF5Manager()
data = manager.load_episode("episode_xxx.hdf5")

state = data['state']    # (N, 7) - 绝对位姿
action = data['action']  # (N, 7) - 相对位姿

print(f"First action (should be near zero): {action[0]}")
print(f"State at first frame: {state[0]}")
```

### 从Action恢复绝对位姿

如果需要从action恢复绝对位姿：

```python
from forceumi.utils.transforms import pose_to_matrix, matrix_to_pose
import numpy as np

# 已知第一帧的state（参考位姿）
reference_state = state[0]  # (7,)

# 从action恢复某一帧的state
def action_to_state(action, reference_state):
    """从相对位姿恢复绝对位姿"""
    # 提取6D pose
    action_6d = action[:6]
    reference_6d = reference_state[:6]
    
    # 转换为变换矩阵
    T_ref = pose_to_matrix(reference_6d)
    T_relative = pose_to_matrix(action_6d)
    
    # 计算绝对变换: T_current = T_ref * T_relative
    T_current = T_ref @ T_relative
    
    # 转换回pose
    current_6d = matrix_to_pose(T_current)
    
    # 添加gripper（使用action中的绝对值）
    return np.append(current_6d, action[6])

# 验证
recovered_state = action_to_state(action[10], reference_state)
print(f"Original state[10]: {state[10]}")
print(f"Recovered state[10]: {recovered_state}")
print(f"Error: {np.linalg.norm(state[10] - recovered_state)}")
```

## 工具函数

### 可用的坐标转换函数

```python
from forceumi.utils.transforms import (
    euler_to_matrix,         # Euler角 -> 旋转矩阵
    matrix_to_euler,         # 旋转矩阵 -> Euler角
    pose_to_matrix,          # 6D pose -> 4x4变换矩阵
    matrix_to_pose,          # 4x4变换矩阵 -> 6D pose
    inverse_transform,       # 变换矩阵的逆
    relative_pose,           # 计算相对位姿
    batch_relative_poses     # 批量计算相对位姿
)
```

### 测试脚本

运行测试验证坐标转换正确性：

```bash
python examples/test_transforms.py
```

## 向后兼容性

**⚠️ 破坏性变更**

版本 0.3.0 之前采集的数据中，action = state。如果需要处理旧数据，可以：

1. **重新计算action**：
```python
from forceumi.utils.transforms import batch_relative_poses

# 加载旧数据
old_data = manager.load_episode("old_episode.hdf5")
state = old_data['state']

# 计算新的action
reference = state[0]
new_action = batch_relative_poses(state, reference)

# 保存更新后的数据
old_data['action'] = new_action
manager.save_episode("updated_episode.hdf5", old_data)
```

2. **在训练时处理**：
```python
# 如果旧数据中action = state
if is_old_format:
    action = batch_relative_poses(state, state[0])
```

## 常见问题

### Q: 为什么gripper保持绝对值？

A: Gripper表示夹爪的开合程度，是一个状态量而不是相对运动量。保持绝对值更符合物理意义。

### Q: 如何可视化相对运动？

A: Action直接表示相对于起始位姿的运动，可以直接绘制轨迹：

```python
import matplotlib.pyplot as plt

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 绘制相对位置轨迹
ax.plot(action[:, 0], action[:, 1], action[:, 2])
ax.set_xlabel('Relative X')
ax.set_ylabel('Relative Y')
ax.set_zlabel('Relative Z')
plt.show()
```

### Q: 数据采集时需要注意什么？

A: 
1. **第一帧很重要**：它定义了整个episode的参考坐标系
2. **预热期**：系统会在正式采集前预热2秒，确保传感器稳定
3. **保持连续**：避免在采集过程中tracker失去追踪

## 技术参考

- Euler角顺序：ZYX (yaw-pitch-roll)
- 变换矩阵：标准4x4齐次变换矩阵
- 角度单位：弧度（**注意**：PyTracker原始输出为度，已自动转换为弧度）
- 位置单位：米
- 角度范围：[-π, π]

## 更多信息

- 坐标转换实现：`forceumi/utils/transforms.py`
- 数据采集实现：`forceumi/collector.py`
- 测试脚本：`examples/test_transforms.py`
- 变更日志：`CHANGELOG.md`

