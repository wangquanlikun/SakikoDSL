class Stack:
    def __init__(self):
        self.stack = []

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        if not self.is_empty():
            return self.stack.pop()
        else:
            raise IndexError("Pop from empty stack")

    def peek(self):
        if not self.is_empty():
            return self.stack[-1]
        else:
            raise IndexError("Peek from empty stack")

    def is_empty(self):
        return len(self.stack) == 0

    def __str__(self):
        return str(self.stack)

class Heap:
    def __init__(self):
        self.heap = {}

    def store(self, address, value):
        self.heap[address] = value

    def load(self, address):
        if address in self.heap:
            return self.heap[address]
        else:
            raise KeyError(f"Address {address} not found in memory")

    def get_new_addr(self):
        return len(self.heap)

    def __str__(self):
        return str(self.heap)

class CodeSegment:
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return str(self.code)

class Memory:
    def __init__(self):
        self.stack = Stack()
        self.heap = Heap()
        self.code = CodeSegment("")

    def __str__(self):
        return f"Memory(stack={self.stack}, heap={self.heap}, code={self.code})"