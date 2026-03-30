import tkinter as tk
from tkinter import filedialog

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('Bank Statement Import')
        self.create_widgets()

    def create_widgets(self):
        self.label = tk.Label(self.root, text='Select Bank Statement:')
        self.label.pack(pady=10)

        self.button = tk.Button(self.root, text='Browse', command=self.load_file)
        self.button.pack(pady=10)

    def load_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        # Add logic to detect Receipt/Payment/Contra and normalize 'Cash in Hand'.
        pass

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()