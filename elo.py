import datetime
from multielo import MultiElo
import numpy as np
import json
import os
import plotext as plt

elo = MultiElo()

data_path = './data/holdem_player_data.json'

def get_data_backup_path():
  time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
  return f"./data/data_backup_{time}.json"

'''
format of data:
[
  {
    'name': 'player_name',
    'current_rating': 1500,
    'rating_history': [1500, 1000, 900],
  }
]
'''

def get_color_by_rating(rating):
  if rating < 1400:
    #green
    return 32
  elif rating < 1600:
    #yellow
    return 33
  else:
    return 31 # red

def get_title_by_rating(rating):
  if rating < 1400:
    return '34=3000'
  elif rating < 1600:
    return 'Exactly Middle'
  else:
    return 'NO ALLIN'


def color_text(text, color):
  return f"\033[{color}m{text}\033[0m"

def get_data():
  try:
    with open(data_path, 'r') as f:
      pass
  except FileNotFoundError:
    with open(data_path, 'w') as f:
      json.dump([], f)
  with open(data_path, 'r') as f:
    data = json.load(f)
  if not data:
    data = []
  return data

def save_data(data):
  with open(data_path, 'w') as f:
    json.dump(data, f)

def register_player(player_name, initial_rating=1500):
  data = get_data()
  for player in data:
    if player['name'] == player_name:
      return
  data.append({
    'name': player_name,
    'current_rating': initial_rating,
    'rating_history': [initial_rating],
  })
  save_data(data)

def display_player(player_name):
  data = get_data()
  cur_player = None
  for player in data:
    if player['name'] == player_name:
      cur_player = player
      break
  
  if cur_player: 
    os.system('cls' if os.name == 'nt' else 'clear')
    colored_title = color_text(get_title_by_rating(cur_player['current_rating']), get_color_by_rating(cur_player['current_rating']))
    cur_rating_display = color_text(f"{cur_player['current_rating']}", get_color_by_rating(cur_player['current_rating']))
    print(f"[-| {colored_title} |-]{cur_player['name']}({cur_rating_display})")
    rating_history = cur_player['rating_history']
    rating_history_display = [color_text(f"{rating}", get_color_by_rating(rating)) for rating in rating_history]
    rating_str = " ".join(rating_history_display)
    print(f"Rating History: {rating_str}")

    max_rating = max(cur_player['rating_history'])
    max_rating_display = color_text(f"{max_rating}", get_color_by_rating(max_rating))
    print(f"Max Rating: {max_rating_display}")
    input("Press any key to continue")
    
    # if len(cur_player['rating_history']) > 100:
    #   rating_history = cur_player['rating_history'][-100:]
    # plt.grid(0, 1)
    plt.plot(rating_history)
    plt.title(f"{cur_player['name']}({cur_player['current_rating']})'s Rating History\n")
    plt.show()
  else:
    print("Player not found")

def get_new_ratings_by_rankings(player_rank_list):
  return elo.get_new_ratings(player_rank_list)

def get_new_ratings_by_rankings_and_scores(ratings, scores, k_factor):
  n = len(ratings)
  win_rates = []
  for i in range(n):
    i_win_rate = 0
    for j in range(n):
      if i == j:
        continue
      win_rate = elo.simulate_win_probabilities([ratings[i], ratings[j]])
      i_win_rate += win_rate[0][0]
    i_win_rate /= (n * (n - 1) / 2)
    win_rates.append(i_win_rate)
  tot_score = np.sum(np.array(scores))
  for i in range(n):
    scores[i] /= tot_score
  new_ratings = []
  k_factor_adjusted = k_factor
  if True:
    k_factor_adjusted = k_factor * n
  for i in range(n):
    new_rating = (scores[i] - win_rates[i]) * k_factor_adjusted + ratings[i]
    new_ratings.append(new_rating)
  return new_ratings

def record_match(players, scores=None, k_factor=32):
  data = get_data()
  rating_list = []
  for player in players:
    found = False
    for i in range(len(data)):
      if data[i]['name'] == player:
        rating_list.append(data[i]['current_rating'])
        found = True
        break
    if not found:
      print(f"Player {player} not found")
      return
  if scores:
    new_ratings = get_new_ratings_by_rankings_and_scores(rating_list, scores, k_factor=k_factor)
  else:
    new_ratings = get_new_ratings_by_rankings(rating_list)
  delta_ratings = new_ratings - np.array(rating_list)
  for i in range(len(players)):
    yellow = '\033[93m'
    green = '\033[92m'
    red = '\033[91m'
    end = '\033[0m'
    change_str = ""
    # limit to 2 decimal places
    rating_list[i] = round(rating_list[i], 3)
    new_ratings[i] = round(new_ratings[i], 3)
    delta_ratings[i] = round(delta_ratings[i], 3)
    if delta_ratings[i] > 0:
      change_str = f"{green}+{delta_ratings[i]}{end}"
    elif delta_ratings[i] < 0:
      change_str = f"{red}{delta_ratings[i]}{end}"
    else:
      change_str = f"{yellow}{delta_ratings[i]}{end}"
    rating_display = color_text(f"{rating_list[i]}", get_color_by_rating(rating_list[i]))
    new_rating_display = color_text(f"{new_ratings[i]}", get_color_by_rating(new_ratings[i]))
    title_colored_display = color_text(get_title_by_rating(rating_list[i]), get_color_by_rating(rating_list[i]))
    new_title_colored_display = color_text(get_title_by_rating(new_ratings[i]), get_color_by_rating(new_ratings[i]))
    format_str = "{:<20}: {:<10} -> {:<10} ({:}) ({:} -> {:})".format(players[i], rating_display, new_rating_display, change_str, title_colored_display, new_title_colored_display)
    print(format_str)
    
  for i in range(len(players)):
    for j in range(len(data)):
      if data[j]['name'] == players[i]:
        data[j]['current_rating'] = new_ratings[i]
        data[j]['rating_history'].append(new_ratings[i])
  save_data(data)

def list_players_by_rank():
  data = get_data()
  data.sort(key=lambda x: x['current_rating'], reverse=True)
  print("{:<8} {:<20} {:<10}".format('Ranking', 'Player', 'Rating'))
  for i in range(len(data)):
    rating_display = color_text(f"{data[i]['current_rating']}", get_color_by_rating(data[i]['current_rating']))
    # title_colored = color_text(get_title_by_rating(data[i]['current_rating']), get_color_by_rating(data[i]['current_rating']))
    print("{:<8} {:<20} {:<10}".format(i+1, data[i]['name'], rating_display))

if __name__ == '__main__':
  while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    print("*****ELO RATING SYSTEM*****")
    print("1. Register Player")
    print("2. Display Player")
    print("3. Record Match")
    print("4. List Players by Rank")
    print("")
    print("0. Save and Exit")
    print("***************************")
    choice = input("Enter your choice: ")
    if not choice.isdigit():
      print("Invalid choice")
    else:
      choice = int(choice)
      if choice < 0 or choice > 4:
        print("Invalid choice")
    if choice == 1:
      player_name = input("Enter player name: ")
      if not player_name or len(player_name) < 3 or len(player_name) > 18:
        print("Invalid player name")
        continue
      register_player(player_name)
    elif choice == 2:
      player_name = input("Enter player name: ")
      display_player(player_name)
    elif choice == 3:
      # enter player names split by space
      if True:
        print("Enter player name (and score if need)\n each line for one player\n and enter 'end' to finish")
        players = []
        scores = []
        while True:
          words = input().split()
          if not words:
            continue
          if words[0] == 'end':
            break
          if len(words) == 1:
            players.append(words[0])
          elif len(words) == 2:
            players.append(words[0])
            if words[1].isdigit():
              scores.append(int(words[1]))
            else:
              print("Invalid score")
              continue
        if not players:
          print("No player entered")
          continue
        if len(scores) > 0 and len(players) != len(scores):
          print("Number of players and scores do not match")
          continue
        if len(scores) == 0:
          record_match(players)
        else:
          record_match(players, scores)
      else:
        words = input("Enter player names split by space: ").split()
        # get last word
        para = words[-1]
        if para == '-s':
          words.pop()
          # get scores
          scores = input("Enter scores split by space: ").split()
          scores = [int(score) for score in scores]
          player_rank_list = words
          if len(player_rank_list) != len(scores):
            print("Number of players and scores do not match")
            continue
          record_match(player_rank_list, scores)
        else:
          player_rank_list = words
          record_match(player_rank_list)
    elif choice == 4:
      list_players_by_rank()
    elif choice == 0:
      break
    input("Press any key to continue")
  # backup
  with open(data_path, 'r') as f:
    data = json.load(f)
  with open(get_data_backup_path(), 'w') as f:
    json.dump(data, f)