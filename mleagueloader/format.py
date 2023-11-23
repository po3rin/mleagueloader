from copy import copy

import pandas as pd

from mahjong.shanten import Shanten
from mahjong.tile import TilesConverter


def tehai_shanten(x):
    if x is None:
        return None

    man = ''.join([v.lower().removesuffix('m') for v in x if v.lower().endswith('m')])
    pin = ''.join([v.lower().removesuffix('p') for v in x if v.lower().endswith('p')])
    sou = ''.join([v.lower().removesuffix('s') for v in x if v.lower().endswith('s')])
    honors = ''.join([v.lower().removesuffix('z') for v in x if v.lower().endswith('z')])

    shanten = Shanten()
    tiles = TilesConverter.string_to_34_array(man=man, pin=pin, sou=sou, honors=honors)
    result = shanten.calculate_shanten(tiles)
    return result

def agari_player(x):
    if x['cmd'] != 'agari':
        return x['player']
    
    if x['args'][0].startswith('ron'):
        return x['args'][1]
    return x['args'][0]

def format_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    # game dataframe ------
    game_df = df[~(df['cmd']=='player')]

    game_df = game_df[~(game_df['cmd']=='dice')]
    game_df = game_df[~(game_df['cmd']=='area')]

    game_df['gameid'] = game_df.apply(lambda x: x['args'][0].replace('id=', '') if x['cmd'] == 'gamestart' else None, axis=1)
    game_df['kyokuid'] = game_df.apply(lambda x: '_'.join(x['args']) if x['cmd'] == 'kyokustart' else None, axis=1)

    player_action = ['haipai', 'tsumo', 'sutehai', 'richi', 'say', 'point']
    game_df['player'] = game_df.apply(lambda x: x['args'][0] if x['cmd'] in player_action else None, axis=1)

    hai_action = ['haipai', 'sutehai']
    game_df['hai'] = game_df.apply(lambda x: x['args'][1] if x['cmd'] in hai_action else None, axis=1)
    game_df['hai'] = game_df.apply(lambda x: x['args'][2] if x['cmd'] == 'tsumo' else x['hai'], axis=1)

    game_df['player'] = game_df.apply(agari_player, axis=1)

    game_df['gameid'] = game_df['gameid'].fillna(method="ffill")
    game_df['kyokuid'] = game_df['kyokuid'].fillna(method="ffill")

    game_df['tsumogiri'] = game_df.apply(lambda x: True if x['cmd'] == 'sutehai' and len(x['args']) > 2 and x['args'][2] == 'tsumogiri' else False, axis=1)
    game_df['nokori_yama'] = game_df.apply(lambda x: x['args'][1] if x['cmd'] == 'tsumo' else None, axis=1)

    game_df['kyokuid'] = game_df.apply(lambda x: x['kyokuid'] if x['cmd'] != 'gamestart' else None, axis=1)

    # player dataframe ------

    player_df = df[df['cmd']=='player']

    player_action = ['player']
    player_df['player'] = player_df.apply(lambda x: x['args'][0] if x['cmd'] in player_action else None, axis=1)
    player_df['name'] = player_df.apply(lambda x: x['args'][1] if x['cmd'] in player_action else None, axis=1)
    player_df['team'] = player_df.apply(lambda x: x['args'][3] if x['cmd'] in player_action else None, axis=1)

    player_df = player_df.drop(columns=['args', 'id', 'cmd'])

    game_id_df = game_df[game_df['cmd']=='gamestart'][['time', 'gameid']]
    game_id_df = game_id_df.drop_duplicates()


    player_df = pd.merge(player_df, game_id_df, on='time', how='inner').drop_duplicates()

    return game_df, player_df


class TehaiGenerator():
    def __init__(self):
        self.player_tehai = {}

    def clear(self):
        self.player_tehai = {}

    def generate(self, df):
        df['tehai'] = None
        for index, row in df.iterrows():
            if row['cmd'] == 'kyokustart':
                self.clear()
            if row['cmd'] in ['tsumo', 'sutehai', 'haipai', 'agari']:
                player = row['player']

                # hapiaは配牌後の状態を保持
                if row['cmd'] == 'haipai':
                    if player not in self.player_tehai:
                        self.player_tehai[player] = []

                    tehai = self.player_tehai[player] + [row['hai'][x:x+2] for x in range(0, len(row['hai']), 2)]
                    self.player_tehai[player] = copy(tehai)
                    df.at[index, 'tehai'] = tehai

                # tehaiはツモ前の状態を保持
                elif row['cmd'] == 'tsumo':
                    tehai = self.player_tehai[player]
                    df.at[index, 'tehai'] = copy(tehai)
                    self.player_tehai[player].append(row['hai'])

                # tehaiは捨てた後の状態を保持
                elif row['cmd'] == 'sutehai':
                    self.player_tehai[player].remove(row['hai'])
                    df.at[index, 'tehai'] = self.player_tehai[player]

                elif row['cmd'] == 'agari':
                    df.at[index, 'tehai'] = self.player_tehai[player]

        return df