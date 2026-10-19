"""Trigger / event / action helpers for RA2/YR mission maps.

Indexes below were taken from WorldAlteringEditor's Default Events.ini /
Actions.ini (section order = game code) and cross-checked against official
YR campaign maps:

events:  6 AttackedByAnyHouse, 7 DestroyedByAnyHouse, 10 AllBuildingsDestroyed,
        11 AllDestroyed, 13 ElapsedTime, 14 TimerExpired, 19 BuiltBuildingType,
        27 GlobalIsSet, 36 LocalIsSet, 37 LocalIsClear
actions: 1 WinnerIs, 2 LoserIs, 4 CreateTeam, 5 DestroyTeam, 7 Reinforcement,
        11 TextTrigger, 14 ChangeHouse, 19 PlaySound, 21 PlaySpeech,
        23 TimerStart, 24 TimerStop, 27 TimerSet, 53 EnableTrigger,
        67 AnnounceWin, 68 AnnounceLose, 80 ReinforcementAtWaypoint

Line formats (verified against WAE Trigger.cs and official maps):
  [Triggers] ID=HOUSE,LINKED,NAME,DISABLED,EASY,NORMAL,HARD,REPEATING
  [Tags]     TAGID=REPEATING,NAME,TRIGGERID
  [Events]   ID=COUNT,(CODE,P1,P2)*          (P1=0, P2=value for our events)
  [Actions]  ID=COUNT,(CODE,P1..P6,P7)*      (P7 written as 'A' when unused;
             for ReinforcementAtWaypoint P7 is the waypoint letter A,B,C...)

Object references in P2: houses are numeric indexes into [Houses]; teams and
triggers are their hex ID strings (this is how official maps and the game do
it — team/trigger names in map files are 8-hex-digit IDs).
"""


def make_trigger(tid: str, tag_id: str, house: str, name: str,
                 events: list[tuple[int, tuple]],
                 actions: list[tuple[int, tuple]],
                 tag_name: str | None = None,
                 repeating: int = 0, disabled: int = 0,
                 linked: str = "<none>") -> dict:
    return dict(id=tid, tag_id=tag_id, house=house, name=name,
                events=events, actions=actions,
                tag_name=tag_name if tag_name is not None else name,
                repeating=repeating, disabled=disabled, linked=linked,
                easy=1, normal=1, hard=1)


def _act(code: int, p2, p3=0, p4=0, p5=0, p6=0, p7="A") -> tuple[int, tuple]:
    return (code, (0, p2, p3, p4, p5, p6, p7))


def act_winner(house_idx: int):
    """WinnerIs(house) — mission is won by `house_idx`."""
    return _act(1, house_idx)


def act_loser(house_idx: int):
    return _act(2, house_idx)


def act_reinforce(team_id: str):
    """Reinforcement(team) — team arrives via its TeamType waypoint/edge."""
    return _act(7, team_id)


def act_reinforce_at_waypoint(team_id: str, waypoint_letter: str):
    """ReinforcementAtWaypoint(team, wp) — wp is the special letter A,B,C..."""
    return _act(80, team_id, p7=waypoint_letter)


def act_text(text: str):
    return _act(11, text)


def act_speech(speech_label: str):
    return _act(21, speech_label)


def act_play_sound(sound_index: int):
    return _act(19, sound_index)


def act_timer_set(seconds: int):
    return _act(27, seconds)


def act_timer_start():
    return _act(23, 0)


def act_enable_trigger(trigger_id: str):
    return _act(53, trigger_id)


def act_reveal_all():
    """RevealAllMap — reveals the whole map to all players."""
    return _act(16, 0)


def act_reveal_waypoint(waypoint_id: int):
    """RevealAroundWaypoint — uncovers the area around a waypoint."""
    return _act(17, waypoint_id)


def act_all_to_hunt(house_idx: int):
    """AllToHunt(house) — all units of the house go attack."""
    return _act(6, house_idx)


def ev_all_destroyed(house_idx: int):
    """Fires when house `house_idx` has no units/structures left."""
    return (11, (0, house_idx))


def ev_all_buildings_destroyed(house_idx: int):
    return (10, (0, house_idx))


def ev_elapsed_time(seconds: int):
    return (13, (0, seconds))


def ev_timer_expired():
    return (14, (0, 0))


def ev_destroyed_by_any():
    """For triggers attached (via tag) to a building/unit."""
    return (7, (0, 0))
