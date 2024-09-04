from espn_api.football import League
import secrets

league = League(league_id=secrets._league_id,
                year=2023,
                espn_s2=secrets._espn_s2,
                swid=secrets._swid)

team_names = [x.team_name for x in league.teams]
n_acq = [x.acquisitions for x in league.teams]

pass