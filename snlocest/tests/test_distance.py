# coding: utf-8

import snlocest.distance


def test_distance():
    p1 = (142.323144141, 43.4438109658)
    p2 = (133.69431925, 34.9088580348)
    assert snlocest.distance.distance == snlocest.distance.vincenty
    assert snlocest.distance.distance(p1, p2) == 1189576.2558712678
    assert snlocest.distance.vincenty(p1, p2) == 1189576.2558712678
    assert snlocest.distance.hubeny(p1, p2) == 1191114.9125639815

def test_cache():
    p1 = (142.323144141, 43.4438109658)
    p2 = (133.69431925, 34.9088580348)

    snlocest.distance.distance.cache_clear()
    for i in range(10):
        snlocest.distance.distance(p1, p2)

    info = snlocest.distance.distance.cache_info()
    assert info.hits == 9
    assert info.misses == 1
