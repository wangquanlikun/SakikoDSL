import json
import threading


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
    print("----loading virtual machine----")
    input_thread = threading.Thread(target=input_func, args=(dsl_parser,))
    input_thread.start()
    dsl_parser.run(source_code)
    print("----script execution completed, press enter to exit----")
    global running
    input_running = False
    input_thread.join()