import json
import threading
import shutil
import sys
sys.path.append("..")

from SakikoDSL.SVM import svmachine

input_running = True

def input_func(parser):
    global input_running
    mode = "command line"
    while input_running:
        if mode == "command line":
            user_input = input()
            if user_input:
                parser.out_input(user_input)
            else:
                break
        elif mode == "GUI":
            pass
        else:
            pass

def load_config():
    with open('config.json') as f:
        config = json.load(f)
    author = config["author"]
    version = config["version"]
    print(f"Author: {author} Copyright")
    print(f"Version: {version}")
    print("Welcome to the customer service robot Staff S(Sakiko)!")
    return config["source"]

if __name__ == '__main__':
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
    input_thread = threading.Thread(target=input_func, args=(dsl_parser,))
    input_thread.start()
    return_code = dsl_parser.run(source_code)
    exit_text = f"Script execution completed with code: {return_code}. Press enter to exit"
    padding = (terminal_width - len(exit_text)) // 2
    print(f"{'-'*padding}{exit_text}{'-'*padding}")
    global running
    input_running = False
    input_thread.join()