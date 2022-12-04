"""Main usage scenario: from game_stuff import *"""


from uuid import uuid4
from abc import ABC, abstractmethod


class _GameAccount:
    
    def __init__(self, username):
        self.user_id = uuid4()
        self.username = username
        self.current_rating = 1
        self.games_count = 0
        self.game_list = []
        self.current_game = None

    def win_game(self):
        game = self._win_lose_common()
        game.winner = self
        game._calculate_rating()

    def lose_game(self):
        game = self._win_lose_common()
        game.winner = game.player1 if game.player1 is self else game.player2
        game._calculate_rating()

    def get_stats(self):
        stats = f"{'Game ID': ^40}{'Game Type': ^16}{'Opponent': ^16}{'Result': ^10}{'Rating': ^10}{'Total Rating': ^14}\n"
        for game in self.game_list:
            opponent = game.player2 if game.player1 is self else game.player1
            result = 'win' if game.winner is self else 'lose'
            if rating := game.ratings[self]:
                rating = f'+{rating}' if result == 'win' else f'-{rating}'
            else:
                rating = '-'
            current_rating = game.player1_current_rating if game.player1 is self else game.player2_current_rating
            stats += f'{str(game.game_id): ^40}{type(game).__name__[1:]: ^16}{opponent.username: ^16}{result: ^10}{rating: ^10}{current_rating: ^14}\n'
        return stats

    def _win_lose_common(self):
        if not self.current_game:
            raise _Game._GameError(f'{self.username} is not playing any game.')
        game = self.current_game
        return game

    def _modify_rating(self, rating):
        return rating


class _TraningGameAccount(_GameAccount):

    def _modify_rating(self, rating):
        return None


class _LiteGameAccount(_GameAccount):

    def _modify_rating(self, rating):
        return rating // 2


class _WinStreakGameAccount(_GameAccount):

    def __init__(self, username):
        super().__init__(username)
        self.winstreak = 0

    def _modify_rating(self, rating):
        if self.current_game:
            if self.current_game.winner is self:
                self.winstreak += 1
            else:
                self.winstreak = 0
        return rating * 2 if self.winstreak >= 3 else rating


class _Game(ABC):

    @abstractmethod
    def __init__(self, player1, player2):
        if self._validate_players(player1, player2):
            self.game_id = uuid4()
            self.player1 = player1
            self.player2 = player2
            self.winner: _GameAccount
            for player in (player1, player2):
                player.current_game = self
                player.game_list.append(self)

    @abstractmethod
    def _calculate_rating(self):
        ...

    def _validate_players(self, *players):
        for player in players:
            if player.current_game:
                raise _Game._GameError(f'Player {player.username} is already in game.')
        return True

    def _save_players_current_rating(self):
        self.player1_current_rating = self.player1.current_rating
        self.player2_current_rating = self.player2.current_rating

    def _close_game(self):
        for player in (self.player1, self.player2):
            player.games_count += 1
            player.current_game = None

    class _GameError(Exception):
        ...


class _StandardGame(_Game):

    def __init__(self, player1, player2, rating):
        if self._validate_rating(rating):
            self.ratings = {player1: rating, player2: rating}
        super().__init__(player1, player2)

    def _validate_rating(self, rating):
        if rating < 0:
            raise ValueError('Rating must be bigger than 0.')
        return True

    def _calculate_rating(self):
        for player in (self.player1, self.player2):
            self.ratings[player] = player._modify_rating(self.ratings[player])
        loser = self.player1 if self.player2 is self.winner else self.player2
        if rating := self.ratings[self.winner]:
            self.winner.current_rating += rating
        if rating := self.ratings[loser]:
            loser.current_rating -= rating
            if loser.current_rating < 1:
                loser.current_rating = 1
        self._save_players_current_rating()
        super()._close_game()


class _TraningGame(_Game):

    def __init__(self, player1, player2):
        super().__init__(player1, player2)
        self.ratings = {player1: None, player2: None}
        self._save_players_current_rating()

    def _calculate_rating(self):
        super()._close_game()


class _HalfRatingGame(_Game):

    def __init__(self, player1, player2, rating_player, rating):
        if self._validate_rating_player((player1, player2), rating_player):
            self.rating_player = rating_player
        if self._validate_rating(rating):
            self.ratings = {player1: None, player2: None}
            self.ratings[self.rating_player] = self.rating_player._modify_rating(rating)
        super().__init__(player1, player2)

    def _calculate_rating(self):
        if self.rating_player is self.winner:
            self.rating_player.current_rating += self.ratings[self.rating_player]
        else:
            self.rating_player.current_rating -= self.ratings[self.rating_player]
            if self.rating_player.current_rating < 1:
                self.rating_player.current_rating = 1
        self._save_players_current_rating()
        super()._close_game()

    def _validate_rating_player(self, players, rating_player):
        if rating_player not in players:
            raise ValueError('Player who plays with rating not in game.')
        return True

    def _validate_rating(self, rating):
        if rating < 0:
            raise ValueError('Rating must be bigger than 0.')
        return True


class GameAccounts:

    """Factory class for generating GameAccount, TraningGameAccount, LiteGameAccount or WinStreakGameAccount objects."""

    @staticmethod
    def GameAccount(username: str):

        """Base Game Account"""

        return _GameAccount(username)

    @staticmethod
    def TraningGameAccount(username: str):

        """Account which does not lose rating"""

        return _TraningGameAccount(username)

    @staticmethod
    def LiteGameAccount(username: str):

        """Account which lose twice lower rating"""

        return _LiteGameAccount(username)

    @staticmethod
    def WinStreakGameAccount(username: str):

        """Account which gain twice more rating when win 3 or more games in a row"""

        return _WinStreakGameAccount(username)


class Games:

    """Factory class for generating StandardGame, TraningGame or HalfRatingGame objects."""

    @staticmethod
    def StandardGame(player1: _GameAccount, player2: _GameAccount, rating: int):

        """Standard game with rating for both players"""

        return _StandardGame(player1, player2, rating)

    @staticmethod
    def TraningGame(player1: _GameAccount, player2: _GameAccount):

        """Traning game without rating for both players"""

        return _TraningGame(player1, player2)

    @staticmethod
    def HalfRatingGame(player1: _GameAccount, player2: _GameAccount, rating_player: _GameAccount, rating: int):

        """Game with rating for only one player"""

        return _HalfRatingGame(player1, player2, rating_player, rating)

