from espn_api.football import League
import secrets

league = League(league_id=secrets._league_id,
                year=2025,
                espn_s2=secrets._espn_s2,
                swid=secrets._swid,
                fetch_league=True)

matchups = league.box_scores(9)

print(matchups[0].home_lineup[0].position)

pass
