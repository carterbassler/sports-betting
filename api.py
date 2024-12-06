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
        game_name = game['game_name']
        game_date = game['game_date']

        for market in game.get('markets', {}).values():
            for outcome in market.get('outcomes', {}).values():
                outcome_id = str(outcome.get('outcome_id'))

                if outcome_id in ev_outcome_ids:

                    ev_opportunity = ev_ops_df[ev_ops_df['outcome_id']
                                               == outcome_id].iloc[0]

                    deeplink = ev_opportunity.get(
                        'ev_model', {}).get('deeplink', '')
                    if "<INSERT_STATE_ID>" in deeplink:
                        deeplink = deeplink.replace("<INSERT_STATE_ID>", "ny")

                    # If there's a match, collect the game
                    matching_games.append({
                        'type': 'prematch',
                        'game_name': game_name,
                        'datetime': str(game_date),
                        'market_type': market.get('display_name'),
                        'book': ev_opportunity.get('book'),
                        'spread': ev_opportunity.get('spread'),
                        'deeplink': ev_opportunity.get('ev_model', {}).get('deeplink'),
                        'american_odds': format_american_odds(ev_opportunity.get('ev_model', {}).get('american_odds')),
                        'outcome_id': outcome_id,
                        'outcome_name': outcome.get('display_name'),
                        'ev': str(round(ev_opportunity.get('ev_model', {}).get('ev', 0), 2)) + '%'
                    })

    if len(matching_games) == 0:
        return
    # Create a DataFrame for matching games
    matching_games_df = pd.DataFrame(matching_games)

    matching_games_df['bet_line'] = matching_games_df.apply(
        lambda row: f"{row['market_type']} {row['outcome_name']} {row['spread'] if row['spread'] != 0 else ''} {row['american_odds']}",
        axis=1
    )

    matching_games_df.drop(
        columns=['market_type', 'outcome_name', 'american_odds', 'spread'], inplace=True)

    result_list = matching_games_df.to_dict(orient='records')

    # print(json.dumps(result_list, indent=4))

    # Return the list of objects (dictionaries)
    return result_list


def match_live_events_to_games_ev():
    # Get all games and EV opportunities
    games = get_all_games(True)  # List of games
    live_ev_ops = get_ev_events('ev_stream')

    # Convert both lists to pandas DataFrames
    games_df = pd.DataFrame(games)  # DataFrame of games
    live_ev_ops_df = pd.DataFrame(live_ev_ops)
    
    if live_ev_ops_df.empty:
        return

    live_ev_ops_df = live_ev_ops_df[live_ev_ops_df['ev_model'].apply(
        lambda x: x.get('ev', 0) > 0.02)]

    live_ev_outcome_ids = set(live_ev_ops_df['outcome_id'])

    matching_games = []

    for game in games_df.to_dict(orient='records'):
        game_name = game['game_name']
        game_date = game['game_date']

        for market in game.get('markets', {}).values():
            for outcome in market.get('outcomes', {}).values():
                outcome_id = str(outcome.get('outcome_id'))

                if outcome_id in live_ev_outcome_ids:

                    live_ev_opportunity = live_ev_ops_df[live_ev_ops_df['outcome_id']
                                                         == outcome_id].iloc[0]

                    deeplink = live_ev_opportunity.get(
                        'ev_model', {}).get('deeplink', '')
                    if "<INSERT_STATE_ID>" in deeplink:
                        deeplink = deeplink.replace("<INSERT_STATE_ID>", "ny")

                    # If there's a match, collect the game
                    matching_games.append({
                        'type': 'live',
                        'game_name': game_name,
                        'datetime': str(game_date),
                        'market_type': market.get('display_name'),
                        'book': live_ev_opportunity.get('book'),
                        'spread': live_ev_opportunity.get('spread'),
                        'deeplink': deeplink,
                        'american_odds': format_american_odds(live_ev_opportunity.get('ev_model', {}).get('american_odds')),
                        'outcome_id': outcome_id,
                        'outcome_name': outcome.get('display_name'),
                        'ev': str(round(live_ev_opportunity.get('ev_model', {}).get('ev', 0), 2)) + '%'
                    })

    if len(matching_games) == 0:
        return
    # Create a DataFrame for matching games
    matching_games_df = pd.DataFrame(matching_games)

    matching_games_df['bet_line'] = matching_games_df.apply(
        lambda row: f"{row['market_type']} {row['outcome_name']} {row['spread'] if row['spread'] != 0 else ''} {row['american_odds']}",
        axis=1
    )

    matching_games_df.drop(
        columns=['market_type', 'outcome_name', 'american_odds', 'spread'], inplace=True)

    result_list = matching_games_df.to_dict(orient='records')

    #print(json.dumps(result_list, indent=4))

    # Return the list of objects (dictionaries)
    return result_list


def match_events_to_games_arb():
    # Get all games and EV opportunities
    games = get_all_games(False)  # List of games
    arb_ops = get_ev_events('arb_stream_prematch')  # List of EV opportunities

    # Convert both lists to pandas DataFrames
    games_df = pd.DataFrame(games)  # DataFrame of games
    arb_ops_df = pd.DataFrame(arb_ops)  # DataFrame of EV opportunities
    
    arb_ops_df = arb_ops_df[arb_ops_df['arb_model'].apply(
        lambda x: x.get('arb_value', 0) > 0.01)]

    arb_outcome_ids = set(
        outcome['outcome_id']
        for arb_model in arb_ops_df['arb_model']
        for outcome in arb_model.get('arb_outcomes', [])
    )

    matching_games = []

    for game in games_df.to_dict(orient='records'):
        game_name = game['game_name']
        game_date = game['game_date']

        for market in game.get('markets', {}).values():
            outcomes = market.get('outcomes',{})
            
            outcome_names = [outcome['display_name'] for outcome in outcomes.values()]
            
            for outcome in market.get('outcomes', {}).values():
                outcome_id = str(outcome.get('outcome_id'))

                if outcome_id in arb_outcome_ids:

                    arb_opportunity = next(
                        (
                            row
                            for _, row in arb_ops_df.iterrows()
                            if any(outcome['outcome_id'] == outcome_id for outcome in row['arb_model']['arb_outcomes'])
                        ),
                        None
                    )

                    # If there's a match, collect the game
                    matching_games.append({
                        'game_name': game_name,
                        'datetime': str(game_date),
                        'market_type': market.get('display_name'),
                        'arb': arb_opportunity['arb_model'].get('arb_value'),
                        'outcome_id': outcome_id,
                        'side1': {
                            'book': arb_opportunity['books'][0],
                            'spread': arb_opportunity['spread'],
                            'deeplink': get_updated_deeplink(arb_opportunity['arb_model']['arb_outcomes'][0]['deeplink']),
                            'american_odds': format_american_odds(arb_opportunity['arb_model']['arb_outcomes'][0]['american_odds']),
                            'outcome_name' : outcome_names[0]
                        },
                        'side2': {
                            'book': arb_opportunity['books'][1],
                            'spread': arb_opportunity['spread'],
                            'deeplink': get_updated_deeplink(arb_opportunity['arb_model']['arb_outcomes'][1]['deeplink']),
                            'american_odds': format_american_odds(arb_opportunity['arb_model']['arb_outcomes'][1]['american_odds']),
                            'outcome_name': outcome_names[1]
                        },
                    })

    if len(matching_games) == 0:
        return
    # Create a DataFrame for matching games
    matching_games_df = pd.DataFrame(matching_games)
    #print(matching_games_df)
    
    matching_games_df['bet_line'] = matching_games_df.apply(
        lambda row: f"{row['market_type']} {str(round(row['arb'] * 100, 2)) + '%'}",
        axis=1
    )

    matching_games_df.drop(
        columns=['market_type', 'arb'], inplace=True)
    
    for index, row in matching_games_df.iterrows():
        # For side1
        side1 = row['side1']
        bet_info = f"{side1['book']} ({side1['outcome_name']} {side1['american_odds']})"
        
        # Add spread if it's non-zero
        if side1['spread'] != 0:
            bet_info = f"{side1['book']} ({side1['outcome_name']} {side1['spread']} {side1['american_odds']})"
        
        side1['bet_info'] = bet_info
        
        # Remove unwanted fields
        del side1['book']
        del side1['outcome_name']
        del side1['american_odds']
        del side1['spread']
        
        # For side2
        side2 = row['side2']
        bet_info = f"{side2['book']} ({side2['outcome_name']} {side2['american_odds']})"
        
        # Add spread if it's non-zero
        if side2['spread'] != 0:
            bet_info = f"{side2['book']} ({side2['outcome_name']} {side2['spread']} {side2['american_odds']})"
        
        side2['bet_info'] = bet_info
        
        # Remove unwanted fields
        del side2['book']
        del side2['outcome_name']
        del side2['american_odds']
        del side2['spread']

    result_list = matching_games_df.to_dict(orient='records')

    #print(json.dumps(result_list, indent=4))

    # Return the list of objects (dictionaries)
    return result_list


def format_american_odds(odds):
    return f"+{odds}" if odds > 0 and not str(odds).startswith("+") else str(odds)

def get_updated_deeplink(deeplink):
    if "<INSERT_STATE_ID>" in deeplink:
        deeplink = deeplink.replace("<INSERT_STATE_ID>", "ny")
    return deeplink

def monitor_api():
    while True:
        #match_events_to_games_ev()
        match_live_events_to_games_ev()
        #match_events_to_games_arb()
        time.sleep(20)


if __name__ == "__main__":
    monitor_api()
