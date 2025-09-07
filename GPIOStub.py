class GPIOStub:
    def __init__(self, pin, mode):
        print(f"[GPIOStub] init pin {pin} as {mode}")
    def write(self, value):
        print(f"[GPIOStub] write {value}")
    def close(self):
        print("[GPIOStub] closed")