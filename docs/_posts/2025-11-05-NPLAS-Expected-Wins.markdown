
We are back with another edition of *NPL Next-gen Stats*, this time demonstrating mathematically that my team is actually good and you are all just super lucky. 

# Expected Wins vs Actual Wins
This next gen stat is pretty simple and it is intended to show your teams performance against the league as a whole instead of your week-to-week match up.
Basically remove the impact of what we call, "Fantasy Defense". 
If $`N_{teams}`$ is the number of teams in the league and $`p_{score}`$ is your scoring position for the week, with zero being the highest score and 11 being the lowest, your expected wins for the week are 
$$w_{exp} = \frac{N_{teams}-p_{score}}{N_{teams}} $$.
In other words, if you have the highest score your expected wins are 1.0. If you have the 7th highest score, your expected wins are 0.5. 

Actual wins are self-explanatory.
The results are shown in the figure below. 

![Expected wins vs actual wins plot](/dash/exp_wins.png)

As expected, my team is gettting screwed. 
Also worth noting, we are collectively underfperforming in matchups against Steve and Troy. 
Pull it together everyone.


# Projected Points vs Actual Points
It is no secret that some of you are excessively beholden to ESPN and whatever nonsense they might publish, but who among us is fooled by the projected scoring? 
Here, the projected points is your total projected points in your starting lineup thus far.
Actual points is your total points scored by starting lineup. 

![Projected points vs actual points plot](/dash/Underperformance.png)
