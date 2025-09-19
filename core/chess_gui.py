import tkinter as tk
class ChessGui:
    def __init__(self):
        root = tk.Tk()
        #root.geometry("500x900")
        canvas = tk.Canvas(root, width=800, height=800)
        canvas.pack()
        for i in range(8):
            for j in range(8):
                if (i+j)%2==0:
                    a = canvas.create_rectangle(1*i, 1*j, 50*i, 50*j, fill='red')
                else:
                    a = canvas.create_rectangle(1*i, 1*j, 50*i, 50*j, fill='blue')

        tk.mainloop()
    def get_move(self):
        pass
test=ChessGui()