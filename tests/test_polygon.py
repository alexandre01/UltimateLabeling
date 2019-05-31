import pytest
from ultimatelabeling.models.polygon import Bbox, Polygon, Keypoints


class TestBbox:

    @pytest.mark.parametrize(
        'xywh, x1y1x2y2', (
                ([0., 0., 10., 10.], [0., 0., 10., 10.]),
                ([-5., -5., 10., 10.], [-5., -5., 5., 5.])
        )
    )
    def test_to_x1y1x2y2(self, xywh, x1y1x2y2):
        bbox = Bbox(*xywh)
        assert bbox.x1y1x2y2.tolist() == x1y1x2y2

    @pytest.mark.parametrize(
        'xywh, xy', (
                ([0., 0., 10., 10.], [5., 5.]),
                ([-5., -5., 1., 1.], [-4.5, -4.5])
        )
    )
    def test_is_inside(self, xywh, xy):
        bbox = Bbox(*xywh)
        assert bbox.is_inside(xy)


class TestKeypoints:

    def test_incorrect_keypoints(self):
        with pytest.raises(AssertionError):
            Keypoints([0., 0.])
