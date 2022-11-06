import pandas as pd


def format_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    game_df = df[~(df['cmd']=='player')]

    game_df = game_df[~(game_df['cmd']=='dice')]
    game_df = game_df[~(game_df['cmd']=='area')]

    game_df['gameid'] = game_df.apply(lambda x: x['args'][0].replace('id=', '') if x['cmd'] == 'gamestart' else None, axis=1)
    game_df['kyokuid'] = game_df.apply(lambda x: '_'.join(x['args']) if x['cmd'] == 'kyokustart' else None, axis=1)

    player_action = ['haipai', 'tsumo', 'sutehai', 'richi', 'say', 'open', 'agari', 'point']
    game_df['player'] = game_df.apply(lambda x: x['args'][0] if x['cmd'] in player_action else None, axis=1)

    hai_action = ['haipai', 'sutehai', 'open']
    game_df['hai'] = game_df.apply(lambda x: x['args'][1] if x['cmd'] in hai_action else None, axis=1)
    game_df['hai'] = game_df.apply(lambda x: x['args'][2] if x['cmd'] == 'tsumo' else x['hai'], axis=1)

    game_df['player'] = game_df.apply(lambda x: x['args'][1] if x['cmd'] == 'agari' else x['player'], axis=1)

    game_df['gameid'] = game_df['gameid'].fillna(method="ffill")
    game_df['kyokuid'] = game_df['kyokuid'].fillna(method="ffill")

    game_df['tsumogiri'] = game_df.apply(lambda x: True if x['cmd'] == 'sutehai' and len(x['args']) > 2 and x['args'][2] == 'tsumogiri' else False, axis=1)
    game_df['nokori_yama'] = game_df.apply(lambda x: x['args'][1] if x['cmd'] == 'tsumo' else None, axis=1)

    game_df['kyokuid'] = game_df.apply(lambda x: x['kyokuid'] if x['cmd'] != 'gamestart' else None, axis=1)


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