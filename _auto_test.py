# 前后端交互测试桩 -- 模拟前端
# 自动化测试脚本

import asyncio
import websockets

async def send_messages(websocket, file_path):
    try:
        # 打开文件并逐行读取
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                # 去掉行尾的换行符
                message = line.strip()
                if message:  # 忽略空行
                    await websocket.send(message)
                    print(f"<<: {message}")
                await asyncio.sleep(4)
    except Exception as e:
        print(f"Error while sending: {e}")

async def receive_messages(websocket):
    try:
        while True:
            message = await websocket.recv()  # 等待服务器的消息
            print(f">>: {message}")
    except Exception as e:
        print(f"Error while receiving: {e}")

async def communicate(file_path, server_url):
    try:
        # 连接到 WebSocket 服务器
        async with websockets.connect(server_url) as websocket:
            # 使用 asyncio.gather 同时运行发送和接收任务
            await asyncio.gather(
                send_messages(websocket, file_path),
                receive_messages(websocket)
            )
    except Exception as e:
        print(f"Connection error: {e}")

def main():
    file_path = "./testScripts/test02.txt"  # 测试脚本输入文件路径
    server_url = "ws://localhost:10043"
    asyncio.run(communicate(file_path, server_url))

if __name__ == "__main__":
    main()
