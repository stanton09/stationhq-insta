"""Caption filters shared by automatic reposts and daily picks."""
import re

_ALWAYS_SKIP = re.compile(
    r"fundrais|birthday|bday|pancake|breakfast|open house|ribbon|ceremony|graduat|promotion|"
    r"retire|condolence|rest in peace|\brip\b|funeral|line of duty death|lodd|in memory|memorial|"
    r"raffle|donat|sponsor|ticket|golf outing|toy drive|blood drive|vote|election|hiring|job posting|"
    r"apply now|merch|t-shirt|giveaway|congrat|welcome our|swearing|sworn in|holiday party|"
    r"wildfire|brush fire|acres|vegetation|prescribed|controlled burn|red flag",
    re.I)
_TRAINING = re.compile(r"training|drill|academy|recruit|class|demo|simulat|exercise", re.I)
# Live-burn training is allowed: real flames in a burn building, acquired structure or burn prop.
LIVE_BURN = re.compile(
    r"live[- ]?burn|live[- ]?fire|burn building|burn tower|burn prop|burn trailer|acquired structure|"
    r"acquired building|flashover|fire behavio|hot drill|fire attack|flames", re.I)


class _Skip:
    """SKIP_WORDS.search(caption): skip fundraisers/memorials/wildland always, and training
    unless it's live-burn training with real fire."""

    def search(self, text):
        return _ALWAYS_SKIP.search(text) or (_TRAINING.search(text) and not LIVE_BURN.search(text))


SKIP_WORDS = _Skip()
# Only repost videos whose caption says it's a real working fire.
FIRE_WORDS = re.compile(
    r"working fire|structure fire|house fire|apartment fire|commercial fire|garage fire|building fire|"
    r"dwelling|\d+(st|nd|rd|th)?[- ]alarm|all[- ]hands|fully involved|heavy fire|fire showing|"
    r"smoke showing|flames|blaze|fire attack|knock(ed)? ?down|interior attack|2-alarm|3-alarm|"
    r"multiple alarm|fire on the|fire in a|fire at a|fire broke out|vehicle fire|car fire|"
    r"10-75|10-77|"  # FDNY radio codes for a working fire / high-rise working fire
    r"live[- ]?burn|live[- ]?fire|burn building|acquired structure|flashover",
    re.I)
