from core.game_builder import GameBuilder

if __name__ == "__main__":

    #create game builder
    builder=GameBuilder()

    #build game
    game = builder.build()

    #run game
    game.play()