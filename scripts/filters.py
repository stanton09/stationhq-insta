"""Caption filters shared by automatic reposts and daily picks."""
import re

SKIP_WORDS = re.compile(
    r"fundrais|birthday|bday|pancake|breakfast|open house|ribbon|ceremony|graduat|promotion|"
    r"retire|condolence|rest in peace|\brip\b|funeral|line of duty death|lodd|in memory|memorial|"
    r"raffle|donat|sponsor|ticket|golf outing|toy drive|blood drive|vote|election|hiring|job posting|"
    r"apply now|merch|t-shirt|giveaway|congrat|welcome our|swearing|sworn in|holiday party"
    r"|training|drill|academy|recruit|class|demo|simulat|exercise|wildfire|brush fire|acres|vegetation|"
    r"prescribed|controlled burn|red flag",
    re.I)
# Only repost videos whose caption says it's a real working fire.
FIRE_WORDS = re.compile(
    r"working fire|structure fire|house fire|apartment fire|commercial fire|garage fire|building fire|"
    r"dwelling|\d+(st|nd|rd|th)?[- ]alarm|all[- ]hands|fully involved|heavy fire|fire showing|"
    r"smoke showing|flames|blaze|fire attack|knock(ed)? ?down|interior attack|2-alarm|3-alarm|"
    r"multiple alarm|fire on the|fire in a|fire at a|fire broke out|vehicle fire|car fire|"
    r"10-75|10-77",  # FDNY radio codes for a working fire / high-rise working fire
    re.I)
