# 前后端交互测试桩 -- 模拟前端
# 自动化测试脚本

import asyncio
import websockets

async def send_messages(file_path, server_url):
    try:
        # 连接到 WebSocket 服务器
        async with websockets.connect(server_url) as websocket:
            # 打开文件并逐行读取
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    # 去掉行尾的换行符
                    message = line.strip()
                    if message:  # 忽略空行
                        await websocket.send(message)
                        print(f"Sent: {message}")
                    await asyncio.sleep(5)
    except Exception as e:
        print(f"Error: {e}")

# 主函数
def main():
    file_path = "./testScripts/test01.txt"  # 测试脚本输入文件路径
    server_url = "ws://localhost:10043"
    asyncio.run(send_messages(file_path, server_url))

if __name__ == "__main__":
    main()
