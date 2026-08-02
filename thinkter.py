import tkinter as tk

root = tk.Tk()
root.title("GridCare-Lite")

tk.Label(root, text="GridCare-Lite Login").pack()
tk.Entry(root).pack()
tk.Button(root, text="Login").pack()

root.mainloop()