import tkinter as tk 
import tkinter.ttk as ttk

    
test_dict = {1 : "one", 2: "tw0", 3:"three"}

t1 = tk.StringVar()
t2 = tk.StringVar()

window = tk.Tk()
style = ttk.Style(window)
style.theme_use("alt")
scroll = tk.Scrollbar(window)
window.geometry("800x400")
display = tk.Button(window, height=2, width=20, text="next",command=take_input)

for key, value in test_dict.items():
    
    textarea = tk.Text(window, height=5, width=50, textvariable = t2)
    label = tk.Label(window, textvariable=t1)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    label.pack(side=tk.TOP)
    textarea.pack(side=tk.TOP)
    display.pack()
    scroll.config(command=textarea.yview)
    textarea.config(yscrollcommand=scroll.set)
    textarea.insert(tk.END,value)
    display.wait_variable(t2)


tk.mainloop()



def take_input(*args):
    pass


if __name__== "__main__":
    check_change()