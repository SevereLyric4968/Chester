from core import game_builder

if __name__ == "__main__":
    #build game
    controller,gui = game_builder.build()

    gui.controller = controller

    #start
    gui.start_update_loop()
    gui.window.mainloop()