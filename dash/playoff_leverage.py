#! /usr/bin/env python3
"""Playoff leverage for the current fantasy week.

For every team, estimate playoff odds conditioned on winning vs. losing its
current-week matchup by Monte Carlo simulation of the rest of the regular
season. Inspired by https://perthirtysix.com/nfl/playoff-leverage

    swing(team)  = P(playoffs | win) - P(playoffs | loss)      [pp]
    leverage(game) = swing(home) + swing(away)

Score model (per team, per week):
    current week : score = live score + N(remaining ESPN projection, sd_rem)
                   sd_rem = sigma * sqrt(remaining_proj / total_proj)
    future weeks : score ~ N(mu_i, sigma)
                   mu_i   = empirical-Bayes shrunk season mean
                   sigma  = pooled within-team weekly sd
Standings: wins, then total points scored (league seed tiebreaker).
Outcomes: playoffs (top 6), first-round bye (seeds 1-2), Sacko seed (bottom 2,
the worst seeds in the double-elimination consolation bracket).
For the Sacko, swing = P(bottom 2 | loss) - P(bottom 2 | win).
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scienceplots  # noqa: F401
from espn_api.football import League

import my_secrets

plt.style.use(["ieee", "no-latex"])


def get_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--year", type=int, default=2026)
    p.add_argument("--week", type=int, default=None,
                   help="matchup week to evaluate (default: ESPN current week)")
    p.add_argument("--sims", type=int, default=200_000)
    p.add_argument("--model", choices=["shrunk", "coinflip"], default="shrunk",
                   help="shrunk: shrunk season means; coinflip: every team equal")
    p.add_argument("--seed", type=int, default=36)
    return p.parse_args()


def load_league(args):
    league = League(league_id=my_secrets._league_id,
                    year=args.year,
                    espn_s2=my_secrets._espn_s2,
                    swid=my_secrets._swid,
                    fetch_league=True)
    week = args.week or league.currentMatchupPeriod
    teams = sorted(league.teams, key=lambda t: t.team_id)
    idx = {t.team_id: i for i, t in enumerate(teams)}
    n_reg = league.settings.reg_season_count
    n_playoff = league.settings.playoff_team_count

    # completed results (weeks before `week`)
    played = np.array([t.scores[: week - 1] for t in teams], dtype=float)
    wins = np.array([sum(o == "W" for o in t.outcomes[: week - 1]) for t in teams], dtype=float)
    points = played.sum(axis=1)

    # remaining schedule: list of (week, i, j) games, each game once
    games = []
    for w in range(week, n_reg + 1):
        for t in teams:
            i, j = idx[t.team_id], idx[t.schedule[w - 1].team_id]
            if i < j:
                games.append((w, i, j))

    # live state of the current week
    live = np.zeros(len(teams))
    proj = np.zeros(len(teams))
    for m in league.box_scores(week):
        for team, score, pr in [(m.home_team, m.home_score, m.home_projected),
                                (m.away_team, m.away_score, m.away_projected)]:
            live[idx[team.team_id]] = score
            proj[idx[team.team_id]] = max(pr, score)

    return dict(teams=teams, names=[" ".join(t.team_name.split()) for t in teams], week=week,
                n_reg=n_reg, n_playoff=n_playoff, played=played, wins=wins,
                points=points, games=games, live=live, proj=proj)


def score_model(d, model):
    s = d["played"]
    n_weeks = s.shape[1]
    grand = s.mean()
    team_mean = s.mean(axis=1)
    sigma = np.sqrt(((s - team_mean[:, None]) ** 2).sum() / (s.size - len(team_mean)))
    # between-team variance of true means (method of moments), floored at 0
    tau2 = max(team_mean.var(ddof=1) - sigma ** 2 / n_weeks, 0.0)
    shrink = tau2 / (tau2 + sigma ** 2 / n_weeks) if tau2 > 0 else 0.0
    mu = grand + shrink * (team_mean - grand)
    if model == "coinflip":
        mu = np.full_like(mu, grand)
        shrink = 0.0
    return mu, sigma, shrink


def simulate(d, mu, sigma, n_sims, rng):
    n = len(d["names"])
    week = d["week"]
    wins = np.tile(d["wins"], (n_sims, 1))
    points = np.tile(d["points"], (n_sims, 1))

    # current-week scores: live + remaining projection with shrinking variance
    rem = np.maximum(d["proj"] - d["live"], 0.0)
    frac = np.divide(rem, d["proj"], out=np.zeros(n), where=d["proj"] > 0)
    cur = d["live"] + rem + sigma * np.sqrt(frac) * rng.standard_normal((n_sims, n))

    cur_win = np.zeros((n_sims, n), dtype=bool)
    for w, i, j in d["games"]:
        if w == week:
            si, sj = cur[:, i], cur[:, j]
        else:
            si = mu[i] + sigma * rng.standard_normal(n_sims)
            sj = mu[j] + sigma * rng.standard_normal(n_sims)
        iw = si > sj
        wins[:, i] += iw
        wins[:, j] += ~iw
        points[:, i] += si
        points[:, j] += sj
        if w == week:
            cur_win[:, i] = iw
            cur_win[:, j] = ~iw

    # rank: wins, then total points (points < 1e4 so this key is exact enough)
    key = wins * 1e5 + points
    rank = (-key).argsort(axis=1).argsort(axis=1)  # 0 = first seed
    return rank, cur_win


def leverage_table(d, made, cur_win, sign=1):
    """made: (sims, teams) bool outcome. sign=-1 for bad outcomes (sacko) so
    swing = P(outcome | loss) - P(outcome | win) stays positive."""
    opp = {}
    for w, i, j in d["games"]:
        if w == d["week"]:
            opp[i], opp[j] = j, i
    rows = []
    for i, name in enumerate(d["names"]):
        w_mask = cur_win[:, i]
        p_win = made[w_mask, i].mean() if w_mask.any() else np.nan
        p_loss = made[~w_mask, i].mean() if (~w_mask).any() else np.nan
        rows.append(dict(team=name, opp=d["names"][opp[i]],
                         record=f"{int(d['wins'][i])}-{d['week'] - 1 - int(d['wins'][i])}",
                         p_win_game=w_mask.mean(),
                         loss=100 * p_loss, current=100 * made[:, i].mean(),
                         win=100 * p_win, swing=round(100 * sign * (p_win - p_loss), 1) + 0.0))
    return pd.DataFrame(rows).sort_values("swing", ascending=False).reset_index(drop=True)


def game_table(d, tab):
    sw = tab.set_index("team")["swing"]
    rows = []
    for w, i, j in d["games"]:
        if w != d["week"]:
            continue
        a, b = d["names"][i], d["names"][j]
        rows.append(dict(game=f"{a} vs {b}", team_a=a, team_b=b,
                         swing_a=sw[a], swing_b=sw[b], leverage=sw[a] + sw[b]))
    return pd.DataFrame(rows).sort_values("leverage", ascending=False).reset_index(drop=True)


def fmt_pct(p):
    """Integer percent, without rounding a live chance to 0% or 100%."""
    # mathtext for < and >: the cmr10 font used by the ieee style maps them to ¡ ¿
    if 0 < p < 0.5:
        return r"$<$1%"
    if 99.5 < p < 100:
        return r"$>$99%"
    return f"{p:.0f}%"


def plot_teams(tab, week, label, fname):
    tab = tab.iloc[::-1].reset_index(drop=True)  # biggest swing on top
    y = np.arange(len(tab))
    fig, ax = plt.subplots(figsize=(6, 7))
    ax.hlines(y, tab["loss"], tab["win"], color="gray", linewidth=3, alpha=0.5)
    ax.scatter(tab["loss"], y, color="red", zorder=3, label="With a loss")
    ax.scatter(tab["current"], y, color="black", marker="|", s=80, zorder=4,
               label="Current chance")
    ax.scatter(tab["win"], y, color="green", zorder=3, label="With a win")

    # row labels: team in bold, record and opponent smaller underneath
    lab = ax.get_yaxis_transform()  # x in axes coords, y in data coords
    small = dict(fontsize=5, textcoords="offset points", ha="center",
                 annotation_clip=False)
    for yi, r in tab.iterrows():
        ax.annotate(r["team"], (-0.02, yi), xycoords=lab, xytext=(0, 1.5),
                    textcoords="offset points", ha="right", va="bottom",
                    fontsize=8, fontfamily="cmb10",  # cmr10 has no bold weight
                    annotation_clip=False)
        ax.annotate(f"({r['record']}) vs {r['opp']}", (-0.02, yi), xycoords=lab,
                    xytext=(0, -1.5), textcoords="offset points", ha="right",
                    va="top", fontsize=6, color="dimgray", annotation_clip=False)
        ax.annotate(f"{r['swing']:+.0f} pp", (1.02, yi), xycoords=lab, va="center",
                    fontsize=7, annotation_clip=False)

        # percentages: current above the tick, loss/win below their markers
        def pct_label(text, x, dy, **kw):
            # left-align labels at the 0% edge so they don't cross the axis
            pos = dict(ha="left", xytext=(-2, dy)) if x < 3 else dict(xytext=(0, dy))
            ax.annotate(text, (x, yi), **{**small, **pos, **kw})

        cur, lo, hi = (fmt_pct(r[k]) for k in ("current", "loss", "win"))
        pct_label(cur, r["current"], 6, va="bottom")
        if lo == hi == cur:  # nothing riding on it: current label says it all
            continue
        if abs(r["win"] - r["loss"]) < 9:
            # markers overlap: loss then win labels beside the pair, on the
            # right normally, on the left near 100% so they stay inside the axes
            side = dict(textcoords="offset points", va="center", fontsize=5,
                        annotation_clip=False)
            if max(r["win"], r["loss"]) < 80:
                t = ax.annotate(lo, (max(r["win"], r["loss"]), yi), xytext=(6, 0),
                                ha="left", color="red", **side)
                ax.annotate(hi, (1, 0.5), xycoords=t, xytext=(3, 0), ha="left",
                            color="green", **side)
            else:
                t = ax.annotate(hi, (min(r["win"], r["loss"]), yi), xytext=(-6, 0),
                                ha="right", color="green", **side)
                ax.annotate(lo, (0, 0.5), xycoords=t, xytext=(-3, 0), ha="right",
                            color="red", **side)
        else:
            pct_label(lo, r["loss"], -6, va="top", color="red")
            pct_label(hi, r["win"], -6, va="top", color="green")

    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.tick_params(axis="y", length=0)
    ax.minorticks_off()
    ax.set_ylim([-0.7, len(tab) - 0.3])
    ax.set_xlim([-2, 102])
    xlab = "Bottom-2 finish (Sacko seed)" if label == "Sacko" else label
    ax.set_xlabel(f"{xlab} chance [%]")
    ax.set_title(f"Week {week} {label if label == 'Sacko' else label.lower()} leverage")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
    fig.subplots_adjust(left=0.36, right=0.9, top=0.95, bottom=0.11)
    fig.savefig(fname)
    plt.close(fig)


def plot_games(gtab, week, label, fname):
    gtab = gtab.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(gtab))
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.barh(y, gtab["swing_a"], color="green", alpha=0.6, edgecolor="gray")
    ax.barh(y, gtab["swing_b"], left=gtab["swing_a"], color="gold", alpha=0.6,
            edgecolor="gray")
    for yi, r in gtab.iterrows():
        ax.annotate(f"{r['leverage']:.0f} pp", (r["leverage"] + 1, yi), va="center",
                    fontsize=6)
    ax.set_yticks(y)
    ax.set_yticklabels(gtab["game"], fontsize=6)
    ax.minorticks_off()
    ax.set_xlim([0, gtab["leverage"].max() * 1.15 + 1])
    ax.set_xlabel(f"Game leverage, sum of both teams' {label.lower()} swing [pp]")
    ax.set_title(f"Week {week}: biggest games")
    fig.tight_layout()
    fig.savefig(fname)
    plt.close(fig)


def main():
    args = get_args()
    rng = np.random.default_rng(args.seed)
    d = load_league(args)
    mu, sigma, shrink = score_model(d, args.model)

    print(f"Week {d['week']} of {d['n_reg']}, {len(d['games'])} games left, "
          f"top {d['n_playoff']} make playoffs, {args.sims:,} sims, model={args.model}")
    print(f"sigma={sigma:.1f}  shrink={shrink:.3f}  "
          f"mu range {mu.min():.1f}-{mu.max():.1f}")

    rank, cur_win = simulate(d, mu, sigma, args.sims, rng)

    tag = f"{args.year}_wk{d['week']}"
    n = len(d["names"])
    outcomes = [("Playoff", rank < d["n_playoff"], 1),
                ("Bye", rank < 2, 1),
                ("Sacko", rank >= n - 2, -1)]  # bottom 2 = worst Sacko seeds
    for label, made, sign in outcomes:
        tab = leverage_table(d, made, cur_win, sign)
        gtab = game_table(d, tab)
        print(f"\n## {label} odds\n")
        print(tab.to_markdown(index=False, floatfmt=".1f"))
        print(f"\n## {label} game leverage\n")
        print(gtab[["game", "swing_a", "swing_b", "leverage"]]
              .to_markdown(index=False, floatfmt=".1f"))
        plot_teams(tab, d["week"], label, f"leverage_{label.lower()}_{tag}.png")
        plot_games(gtab, d["week"], label, f"leverage_games_{label.lower()}_{tag}.png")


if __name__ == "__main__":
    main()
