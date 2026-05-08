
from rblib import r_client, r_account
from .BrowserHandler import resolve_url
def join_game(Account: r_account.Account, IsPrivate: bool, GameId: str):
    str = f"{Account.name} | Roblox"
    client = r_client.RobloxClient(Account)
    if not IsPrivate:
        client.join(int(GameId))
    else:
        if "share?code" in GameId:
            GameId = resolve_url(GameId, Account)
        pscode = GameId[GameId.find("privateServerLinkCode")+len("privateServerLinkCode="):]
        offset = len(GameId) - len(GameId[GameId.find("roblox.com/games/")+len("roblox.com/games/"):])
        gameid = GameId[GameId.find("roblox.com/games/")+len("roblox.com/games/") : GameId[GameId.find("roblox.com/games/")+len("roblox.com/games/"):].find("/") + offset]
        print(f"Pscode: {pscode}")
        print(f"GameID: {gameid}")
        client.join(placeId=int(gameid),psLinkCode=int(pscode))
