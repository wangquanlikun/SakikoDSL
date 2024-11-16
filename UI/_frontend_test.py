# 前后端交互部分测试桩 -- 模拟后端

import asyncio
import websockets
import threading
import os
import webbrowser

connected_clients = set()  # 存储所有连接的客户端

# 处理每个客户端连接
async def handle_connection(websocket, path):
    print(f"客户端已连接: {websocket.remote_address}")
    connected_clients.add(websocket)
    try:
        while True:
            # 接收消息
            message = await websocket.recv()
            print(f"收到来自 {websocket.remote_address} 的消息: {message}")

            # 回显消息
            response = f"服务器收到: {message}"
            if message.startswith("login"):
                await websocket.send("LOGIN_OK")
            else:
                await websocket.send(response)
            print(f"发送回显消息: {response}")
    except websockets.ConnectionClosed:
        print(f"客户端断开连接: {websocket.remote_address}")
    finally:
        connected_clients.remove(websocket)

# 广播消息给所有连接的客户端
async def broadcast_message(message):
    if connected_clients:
        print(f"广播消息: {message}")
        await asyncio.gather(*(client.send(message) for client in connected_clients))
    else:
        print("当前没有连接的客户端。")

# 在事件循环中调度任务
def schedule_message(message, loop):
    asyncio.run_coroutine_threadsafe(broadcast_message(message), loop)

# 服务器主动发送消息
def server_send_message(loop):
    while True:
        message = input("输入要发送给所有客户端的消息 (输入 'exit' 退出): ")
        if message.lower() == "exit":
            print("退出主动消息发送模式。")
            break
        schedule_message(message, loop)

# 启动服务器
async def start_server():
    server = await websockets.serve(handle_connection, "127.0.0.1", 10043)
    print("WebSocket 服务器已启动，监听地址 ws://127.0.0.1:10043")

    # 获取事件循环并启动输入线程
    loop = asyncio.get_running_loop()
    thread = threading.Thread(target=server_send_message, args=(loop,), daemon=True)
    thread.start()

    await server.wait_closed()

# 运行服务器
if __name__ == "__main__":
    file_path = os.path.abspath(r'main.htm')
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    webbrowser.get('chrome').open(f"file:///{file_path}")
    asyncio.run(start_server())
