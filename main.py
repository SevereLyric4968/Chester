from core import game_builder
import config_control_panel

if __name__ == "__main__":
    #build config
    config_control_panel.run()

    #build game
    controller,gui = game_builder.build()

    gui.controller = controller

    #start
    gui.start_update_loop()
    gui.window.mainloop()