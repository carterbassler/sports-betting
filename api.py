import requests
import time
import json
import pandas as pd


def get_all_games(live: bool):
    url = "https://d6ailk8q6o27n.cloudfront.net/livegames"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            games_type = "live_games" if live else "prematch_games"

            prematch_games = data.get("body", {}).get(games_type, [])

            return prematch_games
        else:
            print("Failed to fetch data, status code:", response.status_code)
    except Exception as e:
        print("Error calling API:", e)


def get_ev_events(stream_type):
    url = "https://api.openodds.gg/getData"
    data = {
        "keys": [stream_type],
        "filters": {
            "filtered_sportsbooks": ["PINNY", "BETPARX", "BALLYBET", "NONE", "BETRIVERS"],
            "must_have_sportsbooks": None
        },
        "filter": {}
    }

    # Send POST request
    response = requests.post(url, data=json.dumps(data))

    # IMPLEMENT SEEN BETS SO IT DOESN'T CONTINUOUSLY ADD MORE DATA

    # If the response is successful, return only the payload for the given stream type
    if response.status_code == 200:
        response_json = response.json()

        # Loop through the channels and return the payload for 'ev_stream'
        for channel in response_json:
            if channel.get("channel") == stream_type:
                return channel.get("payload", [])
    else:
        print(f"Error fetching data: {response.status_code}")
        return None


def match_events_to_games_ev():
    # Get all games and EV opportunities
    games = get_all_games(False)  # List of games
    ev_ops = get_ev_events('ev_stream_prematch')  # List of EV opportunities

    # Convert both lists to pandas DataFrames
    games_df = pd.DataFrame(games)  # DataFrame of games
    ev_ops_df = pd.DataFrame(ev_ops)  # DataFrame of EV opportunities

    ev_ops_df = ev_ops_df[ev_ops_df['ev_model'].apply(
        lambda x: x.get('ev', 0) > 0.02)]

    ev_outcome_ids = set(ev_ops_df['outcome_id'])

    matching_games = []

    for game in games_df.to_dict(orient='records'):
        game_id = game['game_id']
        game_name = game['game_name']

        for market in game.get('markets', {}).values():
            for outcome in market.get('outcomes', {}).values():
                outcome_id = str(outcome.get('outcome_id'))

                if outcome_id in ev_outcome_ids:

                    ev_opportunity = ev_ops_df[ev_ops_df['outcome_id']
                                               == outcome_id].iloc[0]

                    # If there's a match, collect the game
                    matching_games.append({
                        'game_name': game_name,
                        'market_type': market.get('display_name'),
                        'book': ev_opportunity.get('book'),
                        'spread': ev_opportunity.get('spread'),
                        'deeplink': ev_opportunity.get('ev_model', {}).get('deeplink'),
                        'american_odds': ev_opportunity.get('ev_model', {}).get('american_odds'),
                        'outcome_id': outcome_id,
                        'outcome_name': outcome.get('display_name'),
                        'ev': ev_opportunity.get('ev_model', {}).get('ev', None),
                    })

    # Create a DataFrame for matching games
    matching_games_df = pd.DataFrame(matching_games)

    matching_games_df['american_odds'] = matching_games_df['american_odds'].apply(
        lambda x: f"+{x}" if x > 0 and not str(x).startswith("+") else str(x)
    )

    matching_games_df['bet_line'] = matching_games_df.apply(
        lambda row: f"{row['market_type']} {row['outcome_name']} {row['spread'] if row['spread'] != 0 else ''} {row['american_odds']}",
        axis=1
    )

    matching_games_df.drop(
        columns=['market_type', 'outcome_name', 'american_odds', 'spread'], inplace=True)

    result_list = matching_games_df.to_dict(orient='records')

    print(json.dumps(result_list, indent=4))

    # Return the list of objects (dictionaries)
    return result_list


def match_events_to_games_ev():
    # Get all games and EV opportunities
    games = get_all_games(False)  # List of games
    ev_ops = get_ev_events('ev_stream_prematch')  # List of EV opportunities
    live_ev_ops = get_ev_events('ev_stream')

    # Convert both lists to pandas DataFrames
    games_df = pd.DataFrame(games)  # DataFrame of games
    ev_ops_df = pd.DataFrame(ev_ops)  # DataFrame of EV opportunities

    ev_ops_df = ev_ops_df[ev_ops_df['ev_model'].apply(
        lambda x: x.get('ev', 0) > 0.02)]

    ev_outcome_ids = set(ev_ops_df['outcome_id'])

    matching_games = []

    for game in games_df.to_dict(orient='records'):
        game_name = game['game_name']

        for market in game.get('markets', {}).values():
            for outcome in market.get('outcomes', {}).values():
                outcome_id = str(outcome.get('outcome_id'))

                if outcome_id in ev_outcome_ids:

                    ev_opportunity = ev_ops_df[ev_ops_df['outcome_id']
                                               == outcome_id].iloc[0]
                    
                    deeplink = ev_opportunity.get('ev_model', {}).get('deeplink', '')
                    print(deeplink)
                    if "<INSERT_STATE_ID>" in deeplink:
                        deeplink = deeplink.replace("<INSERT_STATE_ID>", "ny")

                    # If there's a match, collect the game
                    matching_games.append({
                        'game_name': game_name,
                        'market_type': market.get('display_name'),
                        'book': ev_opportunity.get('book'),
                        'spread': ev_opportunity.get('spread'),
                        'deeplink': ev_opportunity.get('ev_model', {}).get('deeplink'),
                        'american_odds': ev_opportunity.get('ev_model', {}).get('american_odds'),
                        'outcome_id': outcome_id,
                        'outcome_name': outcome.get('display_name'),
                        'ev': ev_opportunity.get('ev_model', {}).get('ev', None),
                    })

    # Create a DataFrame for matching games
    matching_games_df = pd.DataFrame(matching_games)

    matching_games_df['american_odds'] = matching_games_df['american_odds'].apply(
        lambda x: f"+{x}" if x > 0 and not str(x).startswith("+") else str(x)
    )

    matching_games_df['bet_line'] = matching_games_df.apply(
        lambda row: f"{row['market_type']} {row['outcome_name']} {row['spread'] if row['spread'] != 0 else ''} {row['american_odds']}",
        axis=1
    )

    matching_games_df.drop(
        columns=['market_type', 'outcome_name', 'american_odds', 'spread'], inplace=True)

    result_list = matching_games_df.to_dict(orient='records')

    print(json.dumps(result_list, indent=4))

    # Return the list of objects (dictionaries)
    return result_list


# def match_events_to_games_arb():
#     # Get all games and EV opportunities
#     games = get_all_games(False)  # List of games
#     arb_ops = get_ev_events('arb_stream_prematch')  # List of EV opportunities

#     # Convert both lists to pandas DataFrames
#     games_df = pd.DataFrame(games)  # DataFrame of games
#     arb_ops_df = pd.DataFrame(arb_ops)  # DataFrame of EV opportunities

#     arb_outcome_ids = set(
#         outcome['outcome_id']
#         for arb_model in arb_ops_df['arb_model']
#         for outcome in arb_model.get('arb_outcomes', [])
#     )

#     print(arb_outcome_ids)

#     matching_games = []

#     for game in games_df.to_dict(orient='records'):
#         game_name = game['game_name']

#         for market in game.get('markets', {}).values():
#             for outcome in market.get('outcomes', {}).values():
#                 outcome_id = str(outcome.get('outcome_id'))

#                 if outcome_id in arb_outcome_ids:

#                     arb_opportunity = next(
#                         (
#                             row
#                             for _, row in arb_ops_df.iterrows()
#                             if any(outcome['outcome_id'] == outcome_id for outcome in row['arb_model']['arb_outcomes'])
#                         ),
#                         None
#                     )

#                     # If there's a match, collect the game
#                     matching_games.append({
#                         'game_name': game_name,
#                         'market_type': market.get('display_name'),
#                         # First book if available
#                         'books': arb_opportunity['books'],
#                         # Spread from arb_opportunity
#                         'spread': arb_opportunity['spread'],
#                         'deeplink': next(
#                             (outcome.get('deeplink')
#                              for outcome in arb_opportunity['arb_model']['arb_outcomes'] if outcome['outcome_id'] == outcome_id),
#                             None
#                         ),  # Deeplink for the matching outcome_id
#                         'american_odds': next(
#                             (outcome.get('american_odds')
#                              for outcome in arb_opportunity['arb_model']['arb_outcomes'] if outcome['outcome_id'] == outcome_id),
#                             None
#                         ),  # Odds for the matching outcome_id
#                         'outcome_id': outcome_id,
#                         'outcome_name': next(
#                             (outcome.get('display_name')
#                              for outcome in arb_opportunity['arb_model']['arb_outcomes'] if outcome['outcome_id'] == outcome_id),
#                             None
#                         ),  # Display name for the matching outcome_id
#                         # Expected value (ev)
#                         'ev': arb_opportunity['arb_model'].get('arb_value'),
#                     })

#     # Create a DataFrame for matching games
#     matching_games_df = pd.DataFrame(matching_games)

#     matching_games_df['american_odds'] = matching_games_df['american_odds'].apply(
#         lambda x: f"+{x}" if x > 0 and not str(x).startswith("+") else str(x)
#     )

#     matching_games_df['bet_line'] = matching_games_df.apply(
#         lambda row: f"{row['market_type']} {row['outcome_name']} {row['spread'] if row['spread'] != 0 else ''} {row['american_odds']}",
#         axis=1
#     )

#     matching_games_df.drop(
#         columns=['market_type', 'outcome_name', 'american_odds', 'spread'], inplace=True)

#     result_list = matching_games_df.to_dict(orient='records')

#     print(json.dumps(result_list, indent=4))

#     # Return the list of objects (dictionaries)
#     return result_list


def monitor_api():
    while True:
        # "ev_stream_prematch"
        match_events_to_games_ev()
        time.sleep(20)


if __name__ == "__main__":
    monitor_api()
