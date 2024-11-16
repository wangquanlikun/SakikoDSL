import json
import os.path
import threading
import shutil
import asyncio
import websockets
from functools import partial
import webbrowser
import sys
sys.path.append("..")

from SakikoDSL.SVM import svmachine

async def handle_connection(websocket, svm, stop_event):
    svm.set_websocket(websocket)  # 连接建立时设置 websocket

    try:
        async for message in websocket:  # 持续接收来自客户端的消息
            print(f"Message from client: {message}")
            svm.out_input(message)
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    finally:
        print("Connection closed.")
        global input_running
        input_running = False
        stop_event.set()

async def socket_main(svm):
    stop_event = asyncio.Event()
    # 使用 partial 将 svm 和 stop_event 参数传递给 handle_connection
    server = websockets.serve(partial(handle_connection, svm=svm, stop_event=stop_event), "localhost", 10043)
    async with server:
        await stop_event.wait()  # 等待 stop_event 被设置

input_running = True

def input_func(svm):
    global input_running
    mode = "socket server"
    while input_running:
        if mode == "command line":
            user_input = input()
            if user_input:
                svm.out_input(user_input)
            else:
                break
        elif mode == "socket server":
            asyncio.run(socket_main(svm))  # 传递 svm 给 socket_main
            break
        else:
            pass

def load_config():
    # 读取配置文件/返回源代码路径
    with open('config.json') as f:
        config = json.load(f)
    author = config["author"]
    version = config["version"]
    print(f"Author: {author} Copyright")
    print(f"Version: {version}")
    print("Welcome to the customer service robot Staff S(Sakiko)!")
    return config["source"]

def main(test_info):
    # 加载DSL源代码
    source_code_paths = load_config()
    source_code = ""
    for path in source_code_paths:
        with open(path, "r", encoding = "utf-8") as code:
            source_code += code.read() + "\n"
    dsl_parser = svmachine.VirtualMachine()

    loading_text = "Loading virtual machine"
    terminal_width = shutil.get_terminal_size().columns
    padding = (terminal_width - len(loading_text)) // 2
    print(f"{'-'*padding}{loading_text}{'-'*padding}")

    # 单独的线程用于接收用户输入
    input_thread = threading.Thread(target=input_func, args=(dsl_parser,))
    input_thread.start()

    # 在浏览器中打开前端界面
    if not test_info:
        file_path = os.path.abspath(r'UI/main.htm')
        print(file_path)
        chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
        webbrowser.get('chrome').open(f"file:///{file_path}")

    # 运行虚拟机/DSL解释器
    return_code = dsl_parser.run(source_code)
    # 运行结束的返回值
    exit_text = f"Script execution completed with code: {return_code}. Press enter to exit"
    padding = (terminal_width - len(exit_text)) // 2
    print(f"{'-'*padding}{exit_text}{'-'*padding}")

    # 关闭输入线程
    global input_running
    input_running = False
    input_thread.join()

if __name__ == "__main__":
    auto_test_mode = False
    main(auto_test_mode)