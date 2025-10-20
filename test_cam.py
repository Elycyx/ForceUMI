import cv2
import sys

def test_camera(camera_index):
    """测试指定索引的相机"""
    print(f"正在测试相机索引: {camera_index}")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"无法打开相机索引 {camera_index}")
        return False
    
    print(f"相机 {camera_index} 已连接!")
    print("按 'q' 退出， 按 's' 保存截图")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("无法读取帧")
            break
        
        # 在图像上显示相机索引信息
        cv2.putText(frame, f"Camera Index: {camera_index}", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow(f'Camera {camera_index}', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f'camera_{camera_index}_frame_{frame_count}.jpg'
            cv2.imwrite(filename, frame)
            print(f"截图已保存: {filename}")
            frame_count += 1
    
    cap.release()
    cv2.destroyAllWindows()
    return True

def find_available_cameras(max_index_to_check=10):
    """
    尝试查找可用的相机索引。
    它会尝试从0到 max_index_to_check-1 的所有索引。
    """
    available_cameras = []
    print(f"正在尝试查找可用的相机 (从索引 0 到 {max_index_to_check - 1})...")
    for i in range(max_index_to_check):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release() # 释放相机，以便其他程序可以使用
        else:
            print(f"索引 {i} 处未找到相机。")
    return available_cameras

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果提供了参数，测试指定的相机
        camera_index = int(sys.argv[1])
        test_camera(camera_index)
    else:
        # 否则自动查找并逐个测试所有相机
        available_cameras = find_available_cameras(max_index_to_check=30) # 您可以根据需要调整此值
        
        if not available_cameras:
            print("未找到任何可用相机。请检查相机连接或驱动程序。")
        else:
            print("可用的相机索引:", available_cameras)
            for camera_index in available_cameras:
                print(f"\n=== 测试相机 {camera_index} ===")
                success = test_camera(camera_index)
                if success and camera_index != available_cameras[-1]: # Only prompt if it's not the last camera
                    input("按回车继续测试下一个相机...")