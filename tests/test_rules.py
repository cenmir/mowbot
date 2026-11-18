"""Every rule in DESIGN.qmd, one test each."""
import pytest

from mowbot import (Game, LEVELS, Lawn, H_MAX, OutOfBattery, Collision, NotAtStation,
                    NotUnlocked, Progress)
from mowbot.lawn import K_DEFAULT, FLOWERBED
from mowbot import api


def level(n, **kw):
    return Game(LEVELS[n], **kw)


def grown(h, ticks, k=K_DEFAULT):
    """What the engine's Euler loop makes of h after `ticks`; tests expect exactly this."""
    for _ in range(ticks):
        h = h + k * (H_MAX - h)
    return h


# --- the lawn and growth (section 2, 3) ----------------------------------------------------------

def test_growth_is_explicit_euler():
    lawn = Lawn(1, 1, start_height=20.0)
    h = 20.0
    for _ in range(5):
        h = h + K_DEFAULT * (H_MAX - h)
    lawn.grow(5)
    assert lawn[(0, 0)].height == pytest.approx(h)


def test_cut_grass_is_ripe_again_after_some_1800_ticks():
    """About 0.013 mm per tick at the cutting height: ripe (40 mm) after roughly three to four
    laps of a 5x5 lawn, which is what makes waiting for ripe tiles a decision."""
    lawn = Lawn(1, 1, start_height=20.0)
    lawn.grow(1)
    assert lawn[(0, 0)].height == pytest.approx(20.0 + 80 / 6000)
    lawn.grow(1799)
    assert 40.0 < lawn[(0, 0)].height < 42.0


def test_growth_slows_towards_h_max():
    lawn = Lawn(1, 1, start_height=99.0)
    lawn.grow(60000)
    assert lawn[(0, 0)].height < H_MAX
    assert lawn[(0, 0)].height == pytest.approx(H_MAX, abs=1e-3)


def test_scan_is_indexed_x_then_y():
    g = level(7)
    heights = g.scan()
    assert len(heights) == 6 and len(heights[0]) == 6
    g.lawn[(2, 5)].height = 77.0
    assert g.scan()[2][5] == 77.0


# --- driving (section 4) -------------------------------------------------------------------------

def test_starts_at_origin_facing_north():
    g = level(0)
    assert (g.x, g.y, g.heading) == (0, 0, "North")


def test_forward_moves_along_heading_and_edge_is_a_wall():
    g = level(0)
    assert g.forward() and (g.x, g.y) == (0, 1)
    assert g.forward() and (g.x, g.y) == (0, 2)
    assert g.forward() is False and (g.x, g.y) == (0, 2)


def test_turns_cycle_the_four_headings():
    g = level(0)
    g.turn_right(); assert g.heading == "East"
    g.turn_right(); assert g.heading == "South"
    g.turn_left(); g.turn_left(); g.turn_left(); assert g.heading == "West"


def test_backward_cuts_and_costs_twice_the_ticks():
    g = level(0)
    g.forward()                      # cut (0,1)
    t = g.ticks
    g.backward()                     # back onto (0,0), which was never cut
    assert (g.x, g.y) == (0, 0)
    assert g.ticks - t == 20 + 10    # backward 20, cutting 10
    assert g.lawn[(0, 0)].height < 45.0


# --- cutting (section 5, 6) ----------------------------------------------------------------------

def test_start_tile_is_not_cut_until_driven_into_again():
    g = level(0)
    assert g.lawn[(0, 0)].height == 45.0


def test_ripe_window_pays_in_full_and_unripe_pays_half():
    def tokens_for(height):
        g = level(0)
        g.lawn[(0, 1)].height = height
        g.forward()
        return g.tokens
    assert tokens_for(55.0) == pytest.approx(10.0)                        # ripe: full pay
    assert tokens_for(25.0) == pytest.approx(0.5 * (grown(25.0, 20) - 20.0))   # too short
    assert tokens_for(90.0) == pytest.approx(0.5 * 10.0)                  # too tall


def test_one_pass_removes_at_most_ten_mm_and_pays_one_token_per_mm():
    """The move takes 20 ticks, the grass grows meanwhile, then the cut lands."""
    g = level(0)
    g.lawn[(0, 1)].height = 50.0
    g.forward()
    assert g.lawn[(0, 1)].height == pytest.approx(grown(50.0, 20) - 10.0)
    assert g.tokens == pytest.approx(10.0)


def test_never_cuts_below_cutting_height():
    g = level(0)
    g.lawn[(0, 1)].height = 25.0
    g.forward()
    assert g.lawn[(0, 1)].height == pytest.approx(20.0)
    assert g.tokens == pytest.approx(0.5 * (grown(25.0, 20) - 20.0))   # unripe: half pay


def test_blade_on_costs_ticks_even_when_nothing_to_cut():
    g = level(3)
    g.lawn[(0, 1)].height = 5.0          # stays below the cutting height during the move
    g.forward()
    assert g.ticks == 20 and g.tokens == 0
    g.blade_off()
    g.forward()
    assert g.ticks == 30


def test_move_and_turn_ticks():
    g = level(0)
    g.turn_right()
    assert g.ticks == 5


def test_grass_height_looks_at_the_tile_ahead():
    g = level(3)
    g.lawn[(0, 1)].height = 42.0
    assert g.grass_height() == 42.0
    assert g.grass_height("East") == 45.0
    assert g.grass_height("South") == 0.0


# --- battery (level 4) ---------------------------------------------------------------------------

def test_battery_drains_per_move_turn_and_cut():
    g = level(4)
    g.forward()                      # move 1 % + cut 1 %
    assert g.get_battery() == pytest.approx(98.0)
    g.turn_left()
    assert g.get_battery() == pytest.approx(97.0)


def test_battery_does_not_drain_before_level_4():
    g = level(3)
    g.forward()
    assert g.battery == 100.0


def test_empty_battery_stops_the_run():
    g = level(4)
    g.battery = 1.0
    with pytest.raises(OutOfBattery):
        g.forward()


def test_manual_recharge_takes_500_ticks():
    g = level(4)
    g.battery = 5.0
    g.manual_recharge()
    assert g.battery == 100.0 and g.ticks == 500


def test_easy_mode_never_drains():
    g = level(5, easy=True)
    for _ in range(50):
        g.turn_left()
    assert g.battery == 100.0 and g.sharpness == 100.0


# --- blade (level 5) -----------------------------------------------------------------------------

def test_blade_dulls_per_mm_and_income_and_ticks_follow_sharpness():
    g = level(5)
    g.sharpness = 50.0
    g.lawn[(0, 1)].height = 40.0
    g.forward()
    assert g.tokens == pytest.approx(10.0 * 0.5)
    assert g.ticks == 10 + 10 / 0.5
    assert g.sharpness == pytest.approx(50.0 - g.costs.dull_per_mm * 10.0)


def test_sharpness_never_reaches_zero():
    g = level(5)
    g.sharpness = 10.05
    g.lawn[(0, 1)].height = 40.0
    g.forward()
    assert g.sharpness == 10.0


# --- station (level 6) ---------------------------------------------------------------------------

def test_station_charges_in_50_ticks_only_on_the_station():
    g = level(6)
    g.battery = 20.0
    g.charge()
    assert g.battery == 100.0 and g.ticks == 50
    g.forward()
    with pytest.raises(NotAtStation):
        g.charge()
    with pytest.raises(NotAtStation):
        g.sharpen()


# --- unlocks ------------------------------------------------------------------------------------

def test_functions_are_locked_until_their_level():
    g = level(1)
    with pytest.raises(NotUnlocked):
        g.get_x()
    assert level(2).get_x() == 0


def test_unlocks_are_cumulative():
    assert "forward" in LEVELS[13].unlocked
    assert {"for", "while", "if", "def", "list"} <= LEVELS[7].allowed_syntax
    assert "import" not in LEVELS[7].allowed_syntax


def test_progress_banks_tokens_and_unlocks_levels():
    p = Progress()
    g = level(0)
    g.tokens = 250.0
    p.bank(g)
    assert p.can_unlock() and p.unlock()
    assert p.level == 1 and p.tokens == pytest.approx(50.0)
    assert not p.can_unlock()


# --- growth map (level 7) ------------------------------------------------------------------------

def test_sun_and_shade_rates():
    g = level(7)
    assert g.get_growth(5, 0) > g.get_growth(0, 5)      # SE sunny, NW shaded
    assert g.get_growth(5, 0) == pytest.approx(2 * K_DEFAULT)
    assert g.get_growth(0, 5) == pytest.approx(0.5 * K_DEFAULT)


# --- ground and shapes (levels 9, 10) ------------------------------------------------------------

def test_flowerbed_costs_200_tokens_with_the_blade_on():
    g = level(9)
    g.x, g.y, g.heading = 4, 3, "North"
    assert g.get_ground() == FLOWERBED
    g.forward()
    assert g.tokens == pytest.approx(-200.0)


def test_paths_have_no_grass():
    g = level(9)
    assert g.lawn[(0, 1)].height == 0.0 and g.scan()[0][1] == 0.0


def test_house_and_outside_are_walls():
    g = level(10)
    assert (3, 2) not in g.lawn and (3, 3) not in g.lawn      # the house
    assert (4, 7) not in g.lawn                                # the L's missing corner
    g.x, g.y, g.heading = 3, 1, "North"
    assert g.is_clear() is False and g.forward() is False
    assert g.is_clear("West") is True


# --- tall grass and cutting height (level 11) ----------------------------------------------------

def test_tall_grass_cuts_only_five_mm_per_pass():
    g = level(11)
    g.forward()                                  # 80 mm is above 70: a 5 mm pass
    assert g.lawn[(0, 1)].height == pytest.approx(grown(80.0, 20, g.get_growth(0, 1)) - 5.0)
    g.lawn[(0, 2)].height = 55.0
    g.forward()                                  # not above 60: the full 10 mm
    assert g.lawn[(0, 2)].height == pytest.approx(grown(55.0, 20, g.get_growth(0, 2)) - 10.0)


def test_cut_height_is_clamped():
    g = level(11)
    g.set_cut_height(5)
    assert g.cut_height == 20.0
    g.set_cut_height(90)
    assert g.cut_height == 60.0


def test_tall_grass_rule_is_off_before_level_11():
    g = level(10)
    g.lawn[(0, 1)].height = 80.0
    g.forward()
    assert g.lawn[(0, 1)].height == pytest.approx(grown(80.0, 20, g.get_growth(0, 1)) - 10.0)


# --- obstacles (level 12) ------------------------------------------------------------------------

def test_hitting_the_hedgehog_stops_the_run():
    g = level(12)
    g.obstacles[0].x, g.obstacles[0].y = 0, 1
    assert g.is_clear() is False
    with pytest.raises(Collision):
        g.forward()


def test_hedgehog_ambles_as_ticks_pass():
    g = level(12, seed=1)
    start = (g.obstacles[0].x, g.obstacles[0].y)
    for _ in range(20):
        g.turn_left()
    assert (g.obstacles[0].x, g.obstacles[0].y) != start


def test_person_walking_into_the_mower_is_a_hit():
    g = level(12)
    person = g.obstacles[1]
    person.x, person.y = 0, 1
    with pytest.raises(Collision):
        g.move_person("South")


# --- score and api ------------------------------------------------------------------------------

def test_score_is_tokens_per_1000_ticks():
    g = level(0)
    g.forward()                      # 10 mm for 20 ticks
    assert g.score() == pytest.approx(1000 * 10 / 20)


def test_api_binds_to_a_game():
    g = level(2)
    api.bind(g)
    api.forward()
    api.turn_right()
    assert api.get_heading() == api.East and (api.get_x(), api.get_y()) == (0, 1)
