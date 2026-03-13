from core.game_builder import GameBuilder

if __name__ == "__main__":

    #create game builder
    builder=GameBuilder()

    #build game
    controller,gui = builder.build()

    gui.controller = controller
    #start
    gui.start_update_loop()
    gui.window.mainloop()