import json

from SakikoDSL.SVM import svmachine

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
    dsl_parser.run(source_code)